"""Bounded model -> tool -> observation loop with persisted, honest outcomes."""
from datetime import datetime, timedelta, timezone
from .actions import parse_action
from .domain import validate_request
from .models import ModelError
from .storage import ConflictError


class Agent:
    def __init__(self, model, tools, *, max_steps=16, max_tool_calls=12, clock=None, on_event=None):
        if type(max_steps) is not int or type(max_tool_calls) is not int or min(max_steps, max_tool_calls) < 1:
            raise ValueError("execution limits must be positive integers")
        self.model, self.tools, self.store = model, tools, tools.store
        self.max_steps, self.max_tool_calls = max_steps, max_tool_calls
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.on_event = on_event

    def run(self, raw, *, resume=False):
        validation = validate_request(raw, now=self.clock())
        # Look up valid request identities even after deadline, so saved results remain replayable.
        if validation.request is None and validation.errors == ["deadline must be in the future"] and not validation.missing:
            validation = validate_request(raw, now=datetime.min.replace(tzinfo=timezone.utc))
            try:
                existing = self.store.read(raw["request_id"].strip())
                if not existing:
                    raise KeyError()
            except KeyError:
                return {"status": "failed", "reason": "deadline must be in the future"}
        if validation.request is None:
            return {"status": "needs_input" if validation.missing else "failed", "missing": validation.missing, "errors": validation.errors, "trace": []}
        request = validation.request
        if resume:
            try:
                self.store.read(request.request_id)
            except KeyError:
                return {'status':'failed','reason':'resume request not found','trace':[]}
        try:
            state, existed = self.store.start(request)
        except ConflictError as exc:
            return {"status": "failed", "reason": str(exc), "error_code": "idempotency_conflict", "trace": []}
        if existed and state["status"] != "running":
            if not resume or state['status']=='completed':
                return self.output(state, replayed=True)
            with self.store.connect() as conn:
                state=self.store.load(conn,request.request_id)
                error=None
                if state['status'] not in ('incomplete','failed'):
                    error='only incomplete or failed requests can resume'
                elif request.deadline <= self.clock():
                    error='deadline has passed; create a new request'
                elif state.get('resume_count',0)>=3:
                    error='resume_limit reached (3)'
                elif len(state['steps'])>=self.max_tool_calls:
                    error='tool_call_limit reached; cumulative limit is not reset'
                elif state.get('model')!=self.model.name or state.get('mode')!=getattr(self.model,'mode','custom'):
                    error='resume must use the original model and mode'
                if error:
                    return self.output(state,replayed=True) | {'resume_error':error}
                state.setdefault('resume_history',[]).append({'previous_status':state['status'],'reason':state['reason']})
                state['resume_count']=state.get('resume_count',0)+1
                state['status'],state['reason']='running',None
                state['observations'].append({'tool':'resume','ok':True,'summary':'User explicitly resumed after interruption. Reuse successful results and costs; choose the next unfinished action.'})
                self.store.write(conn,state)
        with self.store.connect() as conn:
            state = self.store.load(conn, request.request_id)
            state.setdefault("model", self.model.name)
            state.setdefault("mode", getattr(self.model, "mode", "custom"))
            self.store.write(conn, state)

        for step in range(1, self.max_steps+1):
            state = self.store.read(request.request_id)
            now = self.clock()
            context = {"state": state, "deadline": request.deadline,
                       "effective_now": now+timedelta(minutes=state["elapsed_minutes"]),
                       "step": step, "max_steps": self.max_steps,
                       "remaining_tool_calls": self.max_tool_calls-len(state["steps"])}
            try:
                proposal = parse_action(self.model.decide(context))
            except (ValueError, ModelError) as exc:
                code = "model_error" if isinstance(exc, ModelError) else "invalid_action"
                observation = {"tool": "model", "ok": False, "error_code": code, "summary": str(exc)}
                self.record(request.request_id, step, {"action": code, "args": {}, "why": "模型调用或动作校验失败，回灌观察"}, observation)
                continue
            except Exception:
                # Unknown provider failures remain bounded and must not leak credentials.
                observation = {"tool": "model", "ok": False, "error_code": "model_error", "summary": "unexpected model adapter failure"}
                self.record(request.request_id, step, {"action": "model_error", "args": {}, "why": "模型适配器异常，回灌安全错误摘要"}, observation)
                continue
            if proposal["action"] == "finish":
                obs = {"ok": True, "summary": proposal["args"]["reason"]}
                self.record(request.request_id, step, proposal, obs)
                return self.finish(request.request_id, proposal["args"]["reason"])
            if len(state["steps"]) >= self.max_tool_calls:
                return self.finish(request.request_id, "tool_call_limit reached")
            observation = self.tools.execute(request.request_id, proposal["action"], proposal["args"], now=self.clock(), expected_revision=state["revision"])
            self.record(request.request_id, step, proposal, observation)
            state = self.store.read(request.request_id)
            if state["status"] == "completed":
                return self.output(state)
        return self.finish(request.request_id, "step_limit reached")

    def record(self, request_id, step, proposal, observation):
        with self.store.connect() as conn:
            state = self.store.load(conn, request_id)
            trace = state.setdefault("trace", [])
            if trace:
                trace[-1]["next_action"] = proposal["action"]
            trace.append({"step": len(trace)+1, "action": proposal["action"], "args": proposal["args"],
                          "rationale": proposal["why"], "observation": observation, "next_action": "end"})
            if observation.get("tool") == "model":
                state["observations"].append(observation)
            self.store.write(conn, state)
        if self.on_event:
            self.on_event(proposal, observation)

    def finish(self, request_id, reason):
        with self.store.connect() as conn:
            state = self.store.load(conn, request_id)
            if state["status"] == "running":
                state["status"], state["reason"] = "incomplete", reason
                self.store.write(conn, state)
        return self.output(state)

    def output(self, state, replayed=False):
        saved = next((s["result"] for s in reversed(state["steps"]) if s["tool"] == "save_plan" and s["status"] == "succeeded"), None)
        return {key: state.get(key) for key in ("request_id", "theme", "budget", "deadline", "status", "reason", "steps", "script", "estimate", "actual_tool_cost", "saved_plan_id", "trace", "resume_count", "resume_history")} | {
            "plan": saved,
            "total_cost": state["estimate"]["total_cost"] if state["estimate"] else None,
            "model": state.get("model", self.model.name), "replayed": replayed,
            "mode": state.get("mode", "unknown")}
