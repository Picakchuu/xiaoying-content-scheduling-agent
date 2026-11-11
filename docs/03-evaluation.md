# 评估结果

## 执行方式与实际结果

Python 3.13.5，本地执行以下命令：

```powershell
$env:PYTHONPATH = "src"
python scripts/make_examples.py
```

实际结果：14 组离线用例状态符合预期，31 项 unittest 全部通过。原始汇总见 [summary.json](../examples/summary.json)，测试输出见 [test-results.txt](../examples/test-results.txt)。所有例子是代码实际执行输出；模式为 mock，固定模拟时钟为 2026-11-11 10:00:00+08:00，不是对未来/过去期限的真实执行承诺。

每组目录提供 input.json、output.json、trace.jsonl 和 config.json。

| 场景 | 预期与实际 | 证据 |
|---|---|---|
| 正常 | completed，估算12，保存成功 | [normal](../examples/normal/output.json) |
| 缺预算 | needs_input，无工具调用 | [missing_budget](../examples/missing_budget/output.json) |
| 缺期限 | needs_input，无工具调用 | [missing_deadline](../examples/missing_deadline/output.json) |
| 一次工具失败 | 保留检索成功与生成失败状态，改 lean 后 completed | [tool_failure](../examples/tool_failure/trace.jsonl) |
| 超预算后替代 | 12超预算10，重新生成后8，completed | [over_budget](../examples/over_budget/trace.jsonl) |
| 无可行预算 | incomplete，未保存，保留缺口 | [no_feasible](../examples/no_feasible/output.json) |
| 部分成功 | 使用返回的部分素材，轻量方案 completed | [partial_success](../examples/partial_success/output.json) |
| 时间约束重规划 | premium超时，改 lean 后 completed | [time_replan](../examples/time_replan/trace.jsonl) |
| 无可行时间 | incomplete，未保存 | [time_infeasible](../examples/time_infeasible/output.json) |
| 素材不足 | incomplete，说明缺资料 | [no_materials](../examples/no_materials/output.json) |
| 工具次数上限 | incomplete，保留已成功检索 | [call_limit](../examples/call_limit/output.json) |
| 模型轮次上限 | incomplete，保留已成功检索 | [step_limit](../examples/step_limit/output.json) |
| 相同请求重复 | 重放原结果，未新增工具调用 | [duplicate](../examples/duplicate/output.json) |
| 同标识不同输入 | failed，idempotency_conflict | [idempotency_conflict](../examples/idempotency_conflict/output.json) |

## 单元与集成检查

覆盖预算整数校验、缺失字段、期限时区、指纹等价性、生成后估算失效、保存前重新核时、失败不收费且保留成功状态、唯一保存记录、过期后重放、非法模型动作、提供方异常脱敏与上限、HTTP适配请求/返回结构、CLI输出与退出码。

HTTP适配器测试使用响应替身，不调用真实模型；测试通过不能证明提供方可用或模型效果。CI 配置为 Python 3.11/3.13；本次只确认本地3.13.5通过，尚未检查 GitHub Actions 结果。

## 失败与限制

开发中首次数据库测试受到 Windows tempfile 目录ACL限制；改用仓库内普通临时目录。随后发现测试连接未关闭导致清理失败，改为显式关闭后测试通过。

真实模型评估尚未执行。考核要求的至少两条模型根据不同工具结果调整动作的真实证据仍待补充，不将现有规则 Mock 当作达标证明。建议配置模型后分别执行正常、超预算、故障注入并审阅 Trace，记录模型标识、执行命令、实际结果和失败率。

其他限制：素材检索采用合成标签匹配，脚本由本地模板生成；没有外部制作/支付/发布。未提供失败终态手动续跑、生产并发调度或模型质量统计。实际投入时间与个人贡献由候选人确认，不代填。


## DeepSeek 配置验证

用户指定 `deepseek-v4-pro`。根据[官方接口说明](https://api-docs.deepseek.com/api/create-chat-completion/)设置完整端点、JSON输出及非思考模式，可配置最大输出tokens并检测截断。新增env文件字面值解析、环境变量优先级、非法配置整体拒绝、DeepSeek请求参数和截断返回测试。

真实验证脚本为 `python scripts/evaluate_real.py --env-file .env`。当前缺少本地密钥，尚未执行，配置模板不代表接口已验证。
