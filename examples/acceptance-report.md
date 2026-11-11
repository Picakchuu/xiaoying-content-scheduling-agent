# 集中验收报告

由 `python scripts/build_acceptance_report.py` 从实际文件汇总。输入、输出摘要与关键Trace集中展示，原始输出保留链接。Mock仅证明流程；real表示实际模型动作决策，本地业务工具仍使用合成资料与模板。

## call_limit

输入：
```json
{
  "request_id": "call_limit",
  "theme": "新品活动",
  "budget": 20,
  "deadline": "2026-11-12T10:00:00+08:00"
}
```
实际输出摘要：
```json
{
  "mode": "mock",
  "model": "offline-mock",
  "status": "incomplete",
  "reason": "tool_call_limit reached",
  "total_cost": null,
  "actual_tool_cost": 0,
  "saved_plan_id": null,
  "replayed": false
}
```
[完整输出](call_limit/output.json) · [原始Trace](call_limit/trace.jsonl)

| 步骤 | 动作与参数 | 实际观察摘要 | 后续动作 | 简要依据 |
|---|---|---|---|---|
| 1 | search_materials {"query": "新品活动"} | {"ok": true, "error": null, "summary": "{\"materials\": [{\"id\": \"brand\", \"title\": \"品牌故事素材\", \"tags\": [\"新品\", \"品牌\", \"活动\"], \"summary\": \"合成品牌介绍与产品亮点，可用于活动脚本。\"}, {\"id\": \"tips\", \"title\": \"轻量内容素材\", \"tags\": [\"新品"} | end | 先查找可用素材和制作方案 |

## duplicate

输入：
```json
{
  "request_id": "normal",
  "theme": "新品活动",
  "budget": 20,
  "deadline": "2026-11-12T10:00:00+08:00"
}
```
实际输出摘要：
```json
{
  "mode": "mock",
  "model": "offline-mock",
  "status": "completed",
  "reason": null,
  "total_cost": 12,
  "actual_tool_cost": 1,
  "saved_plan_id": "plan-317b32c143692b99",
  "replayed": true
}
```
[完整输出](duplicate/output.json) · [原始Trace](duplicate/trace.jsonl)

| 步骤 | 动作与参数 | 实际观察摘要 | 后续动作 | 简要依据 |
|---|---|---|---|---|
| 1 | search_materials {"query": "新品活动"} | {"ok": true, "error": null, "summary": "{\"materials\": [{\"id\": \"brand\", \"title\": \"品牌故事素材\", \"tags\": [\"新品\", \"品牌\", \"活动\"], \"summary\": \"合成品牌介绍与产品亮点，可用于活动脚本。\"}, {\"id\": \"tips\", \"title\": \"轻量内容素材\", \"tags\": [\"新品"} | generate_script | 先查找可用素材和制作方案 |
| 2 | generate_script {"variant": "premium", "material_ids": ["brand"]} | {"variant": "premium"} | estimate_cost | 素材部分成功时缩小方案，否则先尝试精剪方案 |
| 3 | estimate_cost {} | {"total_cost": 12, "budget_gap": 0, "feasible": true} | save_plan | 核对当前方案的费用和时间 |
| 4 | save_plan {} | {"plan_id": "plan-317b32c143692b99"} | end | 估算满足预算与截止时间，保存方案 |

## idempotency_conflict

输入：
```json
{
  "request_id": "normal",
  "theme": "新品活动",
  "budget": 9,
  "deadline": "2026-11-12T10:00:00+08:00"
}
```
实际输出摘要：
```json
{
  "status": "failed",
  "reason": "request_id already belongs to different input"
}
```
[完整输出](idempotency_conflict/output.json) · [原始Trace](idempotency_conflict/trace.jsonl)

| 步骤 | 动作与参数 | 实际观察摘要 | 后续动作 | 简要依据 |
|---|---|---|---|---|
| — | 无工具执行 | 输入校验或身份检查已结束 | end | 见实际输出 |

## missing_budget

输入：
```json
{
  "request_id": "missing_budget",
  "theme": "新品活动",
  "deadline": "2026-11-12T10:00:00+08:00"
}
```
实际输出摘要：
```json
{
  "status": "needs_input",
  "missing": [
    "budget"
  ],
  "errors": []
}
```
[完整输出](missing_budget/output.json) · [原始Trace](missing_budget/trace.jsonl)

| 步骤 | 动作与参数 | 实际观察摘要 | 后续动作 | 简要依据 |
|---|---|---|---|---|
| — | 无工具执行 | 输入校验或身份检查已结束 | end | 见实际输出 |

## missing_deadline

输入：
```json
{
  "request_id": "missing_deadline",
  "theme": "新品活动",
  "budget": 20
}
```
实际输出摘要：
```json
{
  "status": "needs_input",
  "missing": [
    "deadline"
  ],
  "errors": []
}
```
[完整输出](missing_deadline/output.json) · [原始Trace](missing_deadline/trace.jsonl)

| 步骤 | 动作与参数 | 实际观察摘要 | 后续动作 | 简要依据 |
|---|---|---|---|---|
| — | 无工具执行 | 输入校验或身份检查已结束 | end | 见实际输出 |

## normal

输入：
```json
{
  "request_id": "normal",
  "theme": "新品活动",
  "budget": 20,
  "deadline": "2026-11-12T10:00:00+08:00"
}
```
实际输出摘要：
```json
{
  "mode": "mock",
  "model": "offline-mock",
  "status": "completed",
  "reason": null,
  "total_cost": 12,
  "actual_tool_cost": 1,
  "saved_plan_id": "plan-317b32c143692b99",
  "replayed": false
}
```
[完整输出](normal/output.json) · [原始Trace](normal/trace.jsonl)

| 步骤 | 动作与参数 | 实际观察摘要 | 后续动作 | 简要依据 |
|---|---|---|---|---|
| 1 | search_materials {"query": "新品活动"} | {"ok": true, "error": null, "summary": "{\"materials\": [{\"id\": \"brand\", \"title\": \"品牌故事素材\", \"tags\": [\"新品\", \"品牌\", \"活动\"], \"summary\": \"合成品牌介绍与产品亮点，可用于活动脚本。\"}, {\"id\": \"tips\", \"title\": \"轻量内容素材\", \"tags\": [\"新品"} | generate_script | 先查找可用素材和制作方案 |
| 2 | generate_script {"variant": "premium", "material_ids": ["brand"]} | {"variant": "premium"} | estimate_cost | 素材部分成功时缩小方案，否则先尝试精剪方案 |
| 3 | estimate_cost {} | {"total_cost": 12, "budget_gap": 0, "feasible": true} | save_plan | 核对当前方案的费用和时间 |
| 4 | save_plan {} | {"plan_id": "plan-317b32c143692b99"} | end | 估算满足预算与截止时间，保存方案 |

## no_feasible

输入：
```json
{
  "request_id": "no_feasible",
  "theme": "新品活动",
  "budget": 2,
  "deadline": "2026-11-12T10:00:00+08:00"
}
```
实际输出摘要：
```json
{
  "mode": "mock",
  "model": "offline-mock",
  "status": "incomplete",
  "reason": "无可行替代方案；当前预算缺口 10，时间缺口 0 分钟",
  "total_cost": 12,
  "actual_tool_cost": 1,
  "saved_plan_id": null,
  "replayed": false
}
```
[完整输出](no_feasible/output.json) · [原始Trace](no_feasible/trace.jsonl)

| 步骤 | 动作与参数 | 实际观察摘要 | 后续动作 | 简要依据 |
|---|---|---|---|---|
| 1 | search_materials {"query": "新品活动"} | {"ok": true, "error": null, "summary": "{\"materials\": [{\"id\": \"brand\", \"title\": \"品牌故事素材\", \"tags\": [\"新品\", \"品牌\", \"活动\"], \"summary\": \"合成品牌介绍与产品亮点，可用于活动脚本。\"}, {\"id\": \"tips\", \"title\": \"轻量内容素材\", \"tags\": [\"新品"} | generate_script | 先查找可用素材和制作方案 |
| 2 | generate_script {"variant": "premium", "material_ids": ["brand"]} | {"variant": "premium"} | estimate_cost | 素材部分成功时缩小方案，否则先尝试精剪方案 |
| 3 | estimate_cost {} | {"total_cost": 12, "budget_gap": 10, "feasible": false} | finish | 核对当前方案的费用和时间 |
| 4 | finish {"reason": "无可行替代方案；当前预算缺口 10，时间缺口 0 分钟"} | {"ok": true, "error": null, "summary": "无可行替代方案；当前预算缺口 10，时间缺口 0 分钟"} | end | 替代方案也无法满足约束，明确返回未完成 |

## no_materials

输入：
```json
{
  "request_id": "no_materials",
  "theme": "火星基地",
  "budget": 20,
  "deadline": "2026-11-12T10:00:00+08:00"
}
```
实际输出摘要：
```json
{
  "mode": "mock",
  "model": "offline-mock",
  "status": "incomplete",
  "reason": "没有相关素材，请补充素材或调整主题",
  "total_cost": null,
  "actual_tool_cost": 0,
  "saved_plan_id": null,
  "replayed": false
}
```
[完整输出](no_materials/output.json) · [原始Trace](no_materials/trace.jsonl)

| 步骤 | 动作与参数 | 实际观察摘要 | 后续动作 | 简要依据 |
|---|---|---|---|---|
| 1 | search_materials {"query": "火星基地"} | {"ok": true, "error": null, "summary": "{\"materials\": [], \"variants\": {\"premium\": {\"production_cost\": 11, \"production_minutes\": 120, \"format\": \"精剪视频\"}, \"lean\": {\"production_cost\": 6, \"production_minut"} | finish | 先查找可用素材和制作方案 |
| 2 | finish {"reason": "没有相关素材，请补充素材或调整主题"} | {"ok": true, "error": null, "summary": "没有相关素材，请补充素材或调整主题"} | end | 检索为空，不能编造资料 |

## over_budget

输入：
```json
{
  "request_id": "over_budget",
  "theme": "新品活动",
  "budget": 10,
  "deadline": "2026-11-12T10:00:00+08:00"
}
```
实际输出摘要：
```json
{
  "mode": "mock",
  "model": "offline-mock",
  "status": "completed",
  "reason": null,
  "total_cost": 8,
  "actual_tool_cost": 2,
  "saved_plan_id": "plan-d8ce24eb9158d6cd",
  "replayed": false
}
```
[完整输出](over_budget/output.json) · [原始Trace](over_budget/trace.jsonl)

| 步骤 | 动作与参数 | 实际观察摘要 | 后续动作 | 简要依据 |
|---|---|---|---|---|
| 1 | search_materials {"query": "新品活动"} | {"ok": true, "error": null, "summary": "{\"materials\": [{\"id\": \"brand\", \"title\": \"品牌故事素材\", \"tags\": [\"新品\", \"品牌\", \"活动\"], \"summary\": \"合成品牌介绍与产品亮点，可用于活动脚本。\"}, {\"id\": \"tips\", \"title\": \"轻量内容素材\", \"tags\": [\"新品"} | generate_script | 先查找可用素材和制作方案 |
| 2 | generate_script {"variant": "premium", "material_ids": ["brand"]} | {"variant": "premium"} | estimate_cost | 素材部分成功时缩小方案，否则先尝试精剪方案 |
| 3 | estimate_cost {} | {"total_cost": 12, "budget_gap": 2, "feasible": false} | generate_script | 核对当前方案的费用和时间 |
| 4 | generate_script {"variant": "lean", "material_ids": ["brand"]} | {"variant": "lean"} | estimate_cost | 观察到超预算或超时，选择可行替代方案并重新估算 |
| 5 | estimate_cost {} | {"total_cost": 8, "budget_gap": 0, "feasible": true} | save_plan | 核对当前方案的费用和时间 |
| 6 | save_plan {} | {"plan_id": "plan-d8ce24eb9158d6cd"} | end | 估算满足预算与截止时间，保存方案 |

## partial_success

输入：
```json
{
  "request_id": "partial_success",
  "theme": "新品活动",
  "budget": 20,
  "deadline": "2026-11-12T10:00:00+08:00"
}
```
实际输出摘要：
```json
{
  "mode": "mock",
  "model": "offline-mock",
  "status": "completed",
  "reason": null,
  "total_cost": 7,
  "actual_tool_cost": 1,
  "saved_plan_id": "plan-a2bb4644ad204148",
  "replayed": false
}
```
[完整输出](partial_success/output.json) · [原始Trace](partial_success/trace.jsonl)

| 步骤 | 动作与参数 | 实际观察摘要 | 后续动作 | 简要依据 |
|---|---|---|---|---|
| 1 | search_materials {"query": "新品活动"} | {"ok": true, "error": null, "summary": "{\"materials\": [{\"id\": \"brand\", \"title\": \"品牌故事素材\", \"tags\": [\"新品\", \"品牌\", \"活动\"], \"summary\": \"合成品牌介绍与产品亮点，可用于活动脚本。\"}], \"variants\": {\"premium\": {\"production_cost\": 1"} | generate_script | 先查找可用素材和制作方案 |
| 2 | generate_script {"variant": "lean", "material_ids": ["brand"]} | {"variant": "lean"} | estimate_cost | 素材部分成功时缩小方案，否则先尝试精剪方案 |
| 3 | estimate_cost {} | {"total_cost": 7, "budget_gap": 0, "feasible": true} | save_plan | 核对当前方案的费用和时间 |
| 4 | save_plan {} | {"plan_id": "plan-a2bb4644ad204148"} | end | 估算满足预算与截止时间，保存方案 |

## resume

输入：
```json
{
  "request_id": "resume-demo",
  "theme": "新品活动",
  "budget": 20,
  "deadline": "2026-11-12T18:00:00+08:00"
}
```
实际输出摘要：
```json
{
  "mode": "mock",
  "model": "offline-mock",
  "status": "completed",
  "reason": null,
  "total_cost": 12,
  "actual_tool_cost": 1,
  "saved_plan_id": "plan-77a7675c365cbecf",
  "replayed": false
}
```
[完整输出](resume/output.json) · [原始Trace](resume/trace.jsonl)

| 步骤 | 动作与参数 | 实际观察摘要 | 后续动作 | 简要依据 |
|---|---|---|---|---|
| 1 | search_materials {"query": "新品活动"} | {"ok": true, "error": null, "summary": "{\"materials\": [{\"id\": \"brand\", \"title\": \"品牌故事素材\", \"tags\": [\"新品\", \"品牌\", \"活动\"], \"summary\": \"合成品牌介绍与产品亮点，可用于活动脚本。\"}, {\"id\": \"tips\", \"title\": \"轻量内容素材\", \"tags\": [\"新品"} | generate_script | 先查找可用素材和制作方案 |
| 2 | generate_script {"variant": "premium", "material_ids": ["brand"]} | {"variant": "premium"} | estimate_cost | 素材部分成功时缩小方案，否则先尝试精剪方案 |
| 3 | estimate_cost {} | {"total_cost": 12, "budget_gap": 0, "feasible": true} | save_plan | 核对当前方案的费用和时间 |
| 4 | save_plan {} | {"ok": false, "error": "injected_failure", "summary": "one-time synthetic failure before execution; no charge"} | save_plan | 估算满足预算与截止时间，保存方案 |
| 5 | save_plan {} | {"plan_id": "plan-77a7675c365cbecf"} | end | 估算满足预算与截止时间，保存方案 |

## step_limit

输入：
```json
{
  "request_id": "step_limit",
  "theme": "新品活动",
  "budget": 20,
  "deadline": "2026-11-12T10:00:00+08:00"
}
```
实际输出摘要：
```json
{
  "mode": "mock",
  "model": "offline-mock",
  "status": "incomplete",
  "reason": "step_limit reached",
  "total_cost": null,
  "actual_tool_cost": 0,
  "saved_plan_id": null,
  "replayed": false
}
```
[完整输出](step_limit/output.json) · [原始Trace](step_limit/trace.jsonl)

| 步骤 | 动作与参数 | 实际观察摘要 | 后续动作 | 简要依据 |
|---|---|---|---|---|
| 1 | search_materials {"query": "新品活动"} | {"ok": true, "error": null, "summary": "{\"materials\": [{\"id\": \"brand\", \"title\": \"品牌故事素材\", \"tags\": [\"新品\", \"品牌\", \"活动\"], \"summary\": \"合成品牌介绍与产品亮点，可用于活动脚本。\"}, {\"id\": \"tips\", \"title\": \"轻量内容素材\", \"tags\": [\"新品"} | end | 先查找可用素材和制作方案 |

## time_infeasible

输入：
```json
{
  "request_id": "time_infeasible",
  "theme": "新品活动",
  "budget": 20,
  "deadline": "2026-11-11T10:10:00+08:00"
}
```
实际输出摘要：
```json
{
  "mode": "mock",
  "model": "offline-mock",
  "status": "incomplete",
  "reason": "无可行替代方案；当前预算缺口 0，时间缺口 111.0 分钟",
  "total_cost": 12,
  "actual_tool_cost": 1,
  "saved_plan_id": null,
  "replayed": false
}
```
[完整输出](time_infeasible/output.json) · [原始Trace](time_infeasible/trace.jsonl)

| 步骤 | 动作与参数 | 实际观察摘要 | 后续动作 | 简要依据 |
|---|---|---|---|---|
| 1 | search_materials {"query": "新品活动"} | {"ok": true, "error": null, "summary": "{\"materials\": [{\"id\": \"brand\", \"title\": \"品牌故事素材\", \"tags\": [\"新品\", \"品牌\", \"活动\"], \"summary\": \"合成品牌介绍与产品亮点，可用于活动脚本。\"}, {\"id\": \"tips\", \"title\": \"轻量内容素材\", \"tags\": [\"新品"} | generate_script | 先查找可用素材和制作方案 |
| 2 | generate_script {"variant": "premium", "material_ids": ["brand"]} | {"variant": "premium"} | estimate_cost | 素材部分成功时缩小方案，否则先尝试精剪方案 |
| 3 | estimate_cost {} | {"total_cost": 12, "budget_gap": 0, "feasible": false} | finish | 核对当前方案的费用和时间 |
| 4 | finish {"reason": "无可行替代方案；当前预算缺口 0，时间缺口 111.0 分钟"} | {"ok": true, "error": null, "summary": "无可行替代方案；当前预算缺口 0，时间缺口 111.0 分钟"} | end | 替代方案也无法满足约束，明确返回未完成 |

## time_replan

输入：
```json
{
  "request_id": "time_replan",
  "theme": "新品活动",
  "budget": 20,
  "deadline": "2026-11-11T11:00:00+08:00"
}
```
实际输出摘要：
```json
{
  "mode": "mock",
  "model": "offline-mock",
  "status": "completed",
  "reason": null,
  "total_cost": 8,
  "actual_tool_cost": 2,
  "saved_plan_id": "plan-7f55a16c15e44a78",
  "replayed": false
}
```
[完整输出](time_replan/output.json) · [原始Trace](time_replan/trace.jsonl)

| 步骤 | 动作与参数 | 实际观察摘要 | 后续动作 | 简要依据 |
|---|---|---|---|---|
| 1 | search_materials {"query": "新品活动"} | {"ok": true, "error": null, "summary": "{\"materials\": [{\"id\": \"brand\", \"title\": \"品牌故事素材\", \"tags\": [\"新品\", \"品牌\", \"活动\"], \"summary\": \"合成品牌介绍与产品亮点，可用于活动脚本。\"}, {\"id\": \"tips\", \"title\": \"轻量内容素材\", \"tags\": [\"新品"} | generate_script | 先查找可用素材和制作方案 |
| 2 | generate_script {"variant": "premium", "material_ids": ["brand"]} | {"variant": "premium"} | estimate_cost | 素材部分成功时缩小方案，否则先尝试精剪方案 |
| 3 | estimate_cost {} | {"total_cost": 12, "budget_gap": 0, "feasible": false} | generate_script | 核对当前方案的费用和时间 |
| 4 | generate_script {"variant": "lean", "material_ids": ["brand"]} | {"variant": "lean"} | estimate_cost | 观察到超预算或超时，选择可行替代方案并重新估算 |
| 5 | estimate_cost {} | {"total_cost": 8, "budget_gap": 0, "feasible": true} | save_plan | 核对当前方案的费用和时间 |
| 6 | save_plan {} | {"plan_id": "plan-7f55a16c15e44a78"} | end | 估算满足预算与截止时间，保存方案 |

## tool_failure

输入：
```json
{
  "request_id": "tool_failure",
  "theme": "新品活动",
  "budget": 20,
  "deadline": "2026-11-12T10:00:00+08:00"
}
```
实际输出摘要：
```json
{
  "mode": "mock",
  "model": "offline-mock",
  "status": "completed",
  "reason": null,
  "total_cost": 7,
  "actual_tool_cost": 1,
  "saved_plan_id": "plan-288df29496a450b7",
  "replayed": false
}
```
[完整输出](tool_failure/output.json) · [原始Trace](tool_failure/trace.jsonl)

| 步骤 | 动作与参数 | 实际观察摘要 | 后续动作 | 简要依据 |
|---|---|---|---|---|
| 1 | search_materials {"query": "新品活动"} | {"ok": true, "error": null, "summary": "{\"materials\": [{\"id\": \"brand\", \"title\": \"品牌故事素材\", \"tags\": [\"新品\", \"品牌\", \"活动\"], \"summary\": \"合成品牌介绍与产品亮点，可用于活动脚本。\"}, {\"id\": \"tips\", \"title\": \"轻量内容素材\", \"tags\": [\"新品"} | generate_script | 先查找可用素材和制作方案 |
| 2 | generate_script {"variant": "premium", "material_ids": ["brand"]} | {"ok": false, "error": "injected_failure", "summary": "one-time synthetic failure before execution; no charge"} | generate_script | 素材部分成功时缩小方案，否则先尝试精剪方案 |
| 3 | generate_script {"variant": "lean", "material_ids": ["brand"]} | {"variant": "lean"} | estimate_cost | 工具失败，保留成功结果并改用轻量方案或重试失败步骤 |
| 4 | estimate_cost {} | {"total_cost": 7, "budget_gap": 0, "feasible": true} | save_plan | 核对当前方案的费用和时间 |
| 5 | save_plan {} | {"plan_id": "plan-288df29496a450b7"} | end | 估算满足预算与截止时间，保存方案 |

## real/18d3a8f54d78/normal

输入：
```json
{
  "request_id": "18d3a8f54d78-normal",
  "theme": "新品活动，优先考虑精剪视频效果",
  "budget": 20,
  "deadline": "2026-11-12T06:38:50.479333+00:00"
}
```
实际输出摘要：
```json
{
  "mode": "real",
  "model": "deepseek-v4-pro",
  "status": "completed",
  "reason": null,
  "total_cost": 12,
  "actual_tool_cost": 1,
  "saved_plan_id": "plan-8f8900fb223abc64",
  "replayed": false
}
```
[完整输出](real/18d3a8f54d78/normal/output.json) · [原始Trace](real/18d3a8f54d78/normal/trace.jsonl)

| 步骤 | 动作与参数 | 实际观察摘要 | 后续动作 | 简要依据 |
|---|---|---|---|---|
| 1 | search_materials {"query": "新品活动 精剪视频"} | {"ok": true, "error": null, "summary": "{\"materials\": [{\"id\": \"brand\", \"title\": \"品牌故事素材\", \"tags\": [\"新品\", \"品牌\", \"活动\"], \"summary\": \"合成品牌介绍与产品亮点，可用于活动脚本。\"}, {\"id\": \"tips\", \"title\": \"轻量内容素材\", \"tags\": [\"新品"} | generate_script | 先检索素材以支持脚本生成 |
| 2 | generate_script {"variant": "premium", "material_ids": ["brand", "tips"]} | {"variant": "premium"} | estimate_cost | 优先精剪视频，使用现有素材生成脚本 |
| 3 | estimate_cost {} | {"total_cost": 12, "budget_gap": 0, "feasible": true} | save_plan | 脚本已生成，估算当前方案总费用以判断预算是否充足 |
| 4 | save_plan {} | {"plan_id": "plan-8f8900fb223abc64"} | end | 方案已估算可行，预算和时间均满足，保存计划。 |

## real/18d3a8f54d78/over_budget

输入：
```json
{
  "request_id": "18d3a8f54d78-over_budget",
  "theme": "新品活动，优先考虑精剪视频效果",
  "budget": 10,
  "deadline": "2026-11-12T06:39:03.871092+00:00"
}
```
实际输出摘要：
```json
{
  "mode": "real",
  "model": "deepseek-v4-pro",
  "status": "completed",
  "reason": null,
  "total_cost": 7,
  "actual_tool_cost": 1,
  "saved_plan_id": "plan-6e41e41da054c7ae",
  "replayed": false
}
```
[完整输出](real/18d3a8f54d78/over_budget/output.json) · [原始Trace](real/18d3a8f54d78/over_budget/trace.jsonl)

| 步骤 | 动作与参数 | 实际观察摘要 | 后续动作 | 简要依据 |
|---|---|---|---|---|
| 1 | search_materials {"query": "新品活动 精剪视频"} | {"ok": true, "error": null, "summary": "{\"materials\": [{\"id\": \"brand\", \"title\": \"品牌故事素材\", \"tags\": [\"新品\", \"品牌\", \"活动\"], \"summary\": \"合成品牌介绍与产品亮点，可用于活动脚本。\"}, {\"id\": \"tips\", \"title\": \"轻量内容素材\", \"tags\": [\"新品"} | generate_script | 先检索素材以确定可用资源 |
| 2 | generate_script {"variant": "lean", "material_ids": ["brand", "tips"]} | {"variant": "lean"} | estimate_cost | 精剪视频超预算，改用轻量短视频方案以控制成本 |
| 3 | estimate_cost {} | {"total_cost": 7, "budget_gap": 0, "feasible": true} | save_plan | 已生成lean脚本，需估算总费用以确认是否在预算内 |
| 4 | save_plan {} | {"plan_id": "plan-6e41e41da054c7ae"} | end | 方案已估算可行且预算时间均满足，保存计划 |

## real/18d3a8f54d78/tool_failure

输入：
```json
{
  "request_id": "18d3a8f54d78-tool_failure",
  "theme": "新品活动，优先考虑精剪视频效果",
  "budget": 10,
  "deadline": "2026-11-12T06:39:16.692756+00:00"
}
```
实际输出摘要：
```json
{
  "mode": "real",
  "model": "deepseek-v4-pro",
  "status": "completed",
  "reason": null,
  "total_cost": 7,
  "actual_tool_cost": 1,
  "saved_plan_id": "plan-7e915e5668e8e5e7",
  "replayed": false
}
```
[完整输出](real/18d3a8f54d78/tool_failure/output.json) · [原始Trace](real/18d3a8f54d78/tool_failure/trace.jsonl)

| 步骤 | 动作与参数 | 实际观察摘要 | 后续动作 | 简要依据 |
|---|---|---|---|---|
| 1 | search_materials {"query": "新品活动 精剪视频"} | {"ok": true, "error": null, "summary": "{\"materials\": [{\"id\": \"brand\", \"title\": \"品牌故事素材\", \"tags\": [\"新品\", \"品牌\", \"活动\"], \"summary\": \"合成品牌介绍与产品亮点，可用于活动脚本。\"}, {\"id\": \"tips\", \"title\": \"轻量内容素材\", \"tags\": [\"新品"} | generate_script | 优先考虑精剪视频效果，先检索相关素材 |
| 2 | generate_script {"variant": "lean", "material_ids": ["brand", "tips"]} | {"ok": false, "error": "injected_failure", "summary": "one-time synthetic failure before execution; no charge"} | generate_script | 精剪视频成本11超预算，改用轻量短视频成本6，先尝试生成脚本 |
| 3 | generate_script {"variant": "lean", "material_ids": ["brand", "tips"]} | {"variant": "lean"} | estimate_cost | 上次生成脚本失败未收费，重试轻量短视频方案 |
| 4 | estimate_cost {} | {"total_cost": 7, "budget_gap": 0, "feasible": true} | save_plan | 脚本已生成，需估算当前方案总费用以判断预算合规性 |
| 5 | save_plan {} | {"plan_id": "plan-7e915e5668e8e5e7"} | end | 估算显示预算和时间均合规，保存当前方案 |

## real-replanning/a5b646045987

输入：
```json
{
  "request_id": "a5b646045987",
  "theme": "新品活动，预算允许时优先精剪视频，超预算可降低制作规格",
  "budget": 10,
  "deadline": "2026-11-12T07:16:03.930327+00:00"
}
```
实际输出摘要：
```json
{
  "mode": "real",
  "model": "deepseek-v4-pro",
  "status": "completed",
  "reason": null,
  "total_cost": 8,
  "actual_tool_cost": 2,
  "saved_plan_id": "plan-b9a357f8e402ddba",
  "replayed": false
}
```
[完整输出](real-replanning/a5b646045987/output.json) · [原始Trace](real-replanning/a5b646045987/trace.jsonl)

| 步骤 | 动作与参数 | 实际观察摘要 | 后续动作 | 简要依据 |
|---|---|---|---|---|
| 1 | search_materials {"query": "新品活动 精剪视频"} | {"ok": true, "error": null, "summary": "{\"materials\": [{\"id\": \"brand\", \"title\": \"品牌故事素材\", \"tags\": [\"新品\", \"品牌\", \"活动\"], \"summary\": \"合成品牌介绍与产品亮点，可用于活动脚本。\"}, {\"id\": \"tips\", \"title\": \"轻量内容素材\", \"tags\": [\"新品"} | generate_script | 优先满足用户精剪视频偏好，先检索相关素材 |
| 2 | generate_script {"variant": "premium", "material_ids": ["brand", "tips"]} | {"variant": "premium"} | estimate_cost | 用户偏好精剪视频，素材充足，先生成脚本 |
| 3 | estimate_cost {} | {"total_cost": 12, "budget_gap": 2, "feasible": false} | generate_script | 已生成premium脚本，需估算总费用确认是否在预算内 |
| 4 | generate_script {"variant": "lean", "material_ids": ["brand", "tips"]} | {"variant": "lean"} | estimate_cost | premium方案超预算2元，改用lean轻量短视频以符合预算并尽量保留视频形式 |
| 5 | estimate_cost {} | {"total_cost": 8, "budget_gap": 0, "feasible": true} | save_plan | 已生成lean脚本，需估算总费用确认是否在预算内 |
| 6 | save_plan {} | {"plan_id": "plan-b9a357f8e402ddba"} | end | lean方案总费用8在预算10内且时间可行，保存计划 |

## 对话补充证据

[真实追问、相对日期与文件输入](chat-live/7ac3833462c8/conversation.json)。对话日志包含用户原话与中文回复，完整执行结果同目录保存。

## 验收边界

失败终态手动续跑已实现，examples/resume包含中断前与续跑后的离线证据。脚本分镜为本地模板；业务费用为模拟单位。真实样本量小，不代表总体成功率。实际投入约2个半小时，个人负责主要需求/设计决策与代码审核修改，AI协助实现；提交SHA使用git rev-parse HEAD取得。
