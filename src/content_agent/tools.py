"""Synthetic business tools. All guards run outside model control."""
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path

DEFAULT_CATALOG = Path(__file__).resolve().parents[2] / "data" / "catalog.json"
TOOL_NAMES = ("search_materials", "generate_script", "estimate_cost", "save_plan")


class ToolError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


class Tools:
    def __init__(self, store, catalog=DEFAULT_CATALOG, faults=None, materials=None):
        self.store = store
        self.catalog = json.loads(Path(catalog).read_text(encoding="utf-8"))
        if materials is not None:
            self.catalog['materials'] = materials
        self.faults = faults or {}
        if any(k not in TOOL_NAMES or v not in ("fail_once", "partial_once") for k, v in self.faults.items()):
            raise ValueError("unsupported fault rule")
        if any(v == "partial_once" and k != "search_materials" for k, v in self.faults.items()):
            raise ValueError("partial_once is supported only for search_materials")

    def execute(self, request_id, name, args, *, now, expected_revision=None):
        if name not in TOOL_NAMES:
            raise ValueError("unknown tool")
        with self.store.connect() as conn:
            state = self.store.load(conn, request_id)
            if expected_revision is not None and state["revision"] != expected_revision:
                return {"ok": False, "tool": name, "error_code": "stale_state", "summary": "state changed; reload before deciding"}
            if state["status"] != "running":
                return {"ok": False, "tool": name, "error_code": "terminal_state", "summary": "request is already terminal"}
            step = {"tool": name, "args": args, "status": "running", "cost": 0}
            state["steps"].append(step)
            try:
                fee = self.catalog["tools"][name]
                if state["actual_tool_cost"] + fee["cost"] > state["budget"]:
                    raise ToolError("budget_exceeded", "tool fee would exceed budget")
                if self._clock(state, now) + timedelta(minutes=fee["minutes"]) > datetime.fromisoformat(state["deadline"]):
                    raise ToolError("deadline_exceeded", "tool cannot finish before deadline")
                # Injected failure happens before execution: no charge, no synthetic time.
                fault = self.faults.get(name) if name not in state["fault_used"] else None
                if fault:
                    state["fault_used"].append(name)
                if fault == "fail_once":
                    raise ToolError("injected_failure", "one-time synthetic failure before execution; no charge")
                result = getattr(self, "_" + name)(state, args, now, conn)
                if fault == "partial_once":
                    result["materials"] = result["materials"][:1]
                    result["partial"] = True
                    state["materials"] = result["materials"]
                state["actual_tool_cost"] += fee["cost"]
                state["elapsed_minutes"] += fee["minutes"]
                observation = dict(ok=True, tool=name, data=result, summary=json.dumps(result, ensure_ascii=False))
                step.update(status="succeeded", result=result, cost=fee["cost"])
            except ToolError as exc:
                observation = dict(ok=False, tool=name, error_code=exc.code, summary=str(exc))
                step.update(status="failed", error=exc.code)
            state["observations"].append(observation)
            self.store.write(conn, state)
            return observation

    @staticmethod
    def _clock(state, now):
        # Synthetic work consumes logical time; do not sleep for simulated minutes.
        return now + timedelta(minutes=state["elapsed_minutes"])

    def _search_materials(self, state, args, now, conn):
        query = args.get("query")
        if not isinstance(query, str) or not query.strip():
            raise ToolError("invalid_args", "query must be non-empty")
        materials = [m for m in self.catalog["materials"] if query in m["title"] or any(t in query for t in m["tags"]) or any(word in m['summary'] for word in query.split() if len(word) >= 2)]
        # Search does not invalidate a successful script; it retains its source snapshot.
        state["materials"] = materials
        return {"materials": materials, "variants": self.catalog["variants"],
                "pricing_note":"检索展示参考制作费；最终费用以estimate_cost报价为准。"}

    def _quoted_variant(self, name):
        variant = dict(self.catalog['variants'][name])
        price = self.catalog.get('final_production_costs', {}).get(name, variant['production_cost'])
        if type(price) is not int or price < 0:
            raise ToolError('invalid_pricing', 'final production cost must be a non-negative integer')
        variant['production_cost'] = price
        return variant

    def _generate_script(self, state, args, now, conn):
        variant = args.get("variant")
        ids = args.get("material_ids")
        if not isinstance(variant, str) or variant not in self.catalog["variants"]:
            raise ToolError("invalid_args", "unknown variant")
        if not isinstance(ids, list) or not ids or any(not isinstance(i, str) for i in ids):
            raise ToolError("invalid_args", "material_ids must be a non-empty string list")
        found = {m["id"]: m for m in state["materials"]}
        if any(i not in found for i in ids):
            raise ToolError("dependency_missing", "materials must come from successful search")
        state["plan_version"] += 1
        state["estimate"] = None
        script = {"version": state["plan_version"], "variant": variant,
                  "sources": [found[i] for i in ids],
                  "text": f"开场：{state['theme']}。展示：" + "；".join(found[i]["summary"] for i in ids) + " 结尾：邀请参与活动。"}
        script['storyboard'] = [
            {'section':'开场', 'visual':'主题标题和产品主画面', 'copy':state['theme']},
            {'section':'内容展示', 'visual':'素材画面配要点字幕', 'copy':'；'.join(found[i]['summary'] for i in ids)},
            {'section':'行动引导', 'visual':'活动说明卡片', 'copy':'了解活动详情；具体权益与投放渠道待运营确认'}]
        state["script"] = script
        return script

    def _estimate_cost(self, state, args, now, conn):
        if not state["script"]:
            raise ToolError("dependency_missing", "generate a script before estimating")
        variant = self._quoted_variant(state["script"]["variant"])
        total = state["actual_tool_cost"] + variant["production_cost"]
        finish = self._clock(state, now) + timedelta(minutes=variant["production_minutes"])
        deadline = datetime.fromisoformat(state["deadline"])
        result = {"version": state["plan_version"], "spent_tool_cost": state["actual_tool_cost"],
                  "remaining_plan_cost": variant["production_cost"], "total_cost": total,
                  "budget_gap": max(0, total-state["budget"]),
                  "estimated_finish": finish.isoformat(),
                  "time_gap_minutes": max(0, (finish-deadline).total_seconds()/60),
                  "feasible": total <= state["budget"] and finish <= deadline}
        state["estimate"] = result
        return result

    def _save_plan(self, state, args, now, conn):
        estimate = state["estimate"]
        if not estimate or estimate["version"] != state["plan_version"]:
            raise ToolError("dependency_missing", "estimate current script before saving")
        variant = self._quoted_variant(state["script"]["variant"])
        finish = self._clock(state, now) + timedelta(minutes=variant["production_minutes"])
        total = state["actual_tool_cost"] + variant["production_cost"]
        if total > state["budget"]:
            raise ToolError("budget_exceeded", f"budget gap: {total-state['budget']}")
        if finish > datetime.fromisoformat(state["deadline"]):
            raise ToolError("deadline_exceeded", "plan no longer fits deadline")
        plan_id = "plan-" + hashlib.sha256(state["request_id"].encode()).hexdigest()[:16]
        payload = {"plan_id": plan_id, "theme": state["theme"], "script": state["script"],
                   "objective":"围绕活动主题输出一份可交接制作的内容方案，不承诺未经验证的转化效果",
                   "deliverables":[variant['format']+'内容草案', '分镜与文案', '素材来源清单', '费用与时间估算'],
                   "pending_confirmation":['目标受众和投放渠道', '实际活动权益及效果指标'],
                   "estimate": {**estimate, "estimated_finish": finish.isoformat()},
                   "tasks": [{"name": "素材检索", "status": "succeeded"},
                             {"name": "脚本生成", "status": "succeeded"},
                             {"name": "内容制作", "status": "pending", **variant}]}
        conn.execute("INSERT INTO plans VALUES (?, ?, ?)", (state["request_id"], plan_id, json.dumps(payload, ensure_ascii=False)))
        state["saved_plan_id"] = plan_id
        state["status"] = "completed"
        return payload
