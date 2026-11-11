# 评估结果

## 执行方式与实际结果

Python 3.13.5，本地执行以下命令：

```powershell
$env:PYTHONPATH = "src"
python scripts/make_examples.py
```

实际结果：14 组离线用例状态符合预期，42 项 unittest 全部通过。原始汇总见 [summary.json](../examples/summary.json)，测试输出见 [test-results.txt](../examples/test-results.txt)。所有例子是代码实际执行输出；模式为 mock，固定模拟时钟为 2026-11-11 10:00:00+08:00，不是对未来/过去期限的真实执行承诺。

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

已完成下面记录的3组真实模型运行。正常结果后保存与失败结果后模型主动重试构成不同执行路径；早期三组真实记录没有覆盖估算超支后的替代方案重规划，现已由下方独立报价变化场景补齐，不把离线12→8路径描述成真实模型证据。

其他限制：素材检索采用合成标签匹配，脚本由本地模板生成；没有外部制作/支付/发布。未提供失败终态手动续跑、生产并发调度或模型质量统计。实际投入约2小时，个人贡献与AI工作边界见docs/04-ai-usage.md。


## DeepSeek 配置验证

用户指定 `deepseek-v4-pro`。根据[官方接口说明](https://api-docs.deepseek.com/api/create-chat-completion/)设置完整端点、JSON输出及非思考模式，可配置最大输出tokens并检测截断。新增env文件字面值解析、环境变量优先级、非法配置整体拒绝、DeepSeek请求参数和截断返回测试。

真实验证命令为 `python scripts/evaluate_real.py --env-file .env`，本轮使用用户本地密钥实际执行；密钥未提交。


## 真实模型实际结果

服务：DeepSeek，模型：deepseek-v4-pro，非思考模式，JSON输出，temperature=0.1，max_tokens=3000。使用真实时钟、未来24小时期限、独立SQLite数据库；没有强制模型动作或手工修改输出。

原始运行目录：[18d3a8f54d78](../examples/real/18d3a8f54d78/summary.json)，状态/费用核对结果见 [review.json](../examples/real/18d3a8f54d78/review.json)。各场景的config.json记录开始时间、故障和执行上限，input/output/trace均为实际文件。

| 场景 | 实际结果 | Trace |
|---|---|---|
| 正常、预算20 | premium，4次工具调用，1+11=12，completed | [normal](../examples/real/18d3a8f54d78/normal/trace.jsonl) |
| 预算10 | 模型在检索后提前选择lean，4次调用，1+6=7，completed | [over_budget](../examples/real/18d3a8f54d78/over_budget/trace.jsonl) |
| 生成工具一次失败、预算10 | lean首次生成失败，模型观察未收费后重试lean，5次调用，1+6=7，completed | [tool_failure](../examples/real/18d3a8f54d78/tool_failure/trace.jsonl) |

核对通过：费用等于成功工具收费之和加剩余制作费，均未超预算；保存ID与实际保存结果一致；故障步骤为failed且费用0，前序检索为succeeded，未重复检索。故障恢复由真实模型再次提出动作，执行器没有自动重试工具。

注意：目录名over_budget表示测试意图，不表示实际发生超支。模型主动规避了12单位方案。此次故障恢复是重试相同方案，不是选择另一制作方式。真实模型预算超限后改选已由后续场景覆盖，部分成功后的真实重规划及多次运行稳定性仍待评估；3次均成功不等于总体成功率为100%。


## v0.2 对话验证与改进

新增追问后执行、相对日期、附件schema/大小、附件变化指纹冲突、实际来源注入、EOF退出、解析修正失败禁止执行旧草稿、模型耗时后的期限复核等测试，当前共42项通过。

真实模型执行两轮相同多轮场景：附加本地合成JSON素材，先只输入新品推广和短视频偏好，系统追问预算/期限，补充“预算10模拟单位，明天下午6点”后执行，并重复重放。

第一轮 [821cb69f9a7e](../examples/chat-live/821cb69f9a7e/conversation.json) 完成了输入/素材/保存流程，但选择micro图文，没有满足短视频偏好；原始证据保留。补充“有可行方案时优先满足内容形式，而不是一味最便宜”的提示后，第二轮 [7ac3833462c8](../examples/chat-live/7ac3833462c8/conversation.json) 选择lean轻量短视频，费用7，保存成功。检查结果见 [review.json](../examples/chat-live/7ac3833462c8/review.json)。重复重放没有新增请求或业务工具调用。

这仅是一个偏好问题的单次改进验证，不保证所有自然语言理解正确。对话内容会因模型和时间变化而不同；重要信息在执行前由用户核对。对话样本自身不覆盖真实预算超限后重规划，该路径另见后续报价变化样本。


## 交付整理

本地模板方案补充分镜、交付物和待确认项，不编造目标人群、权益或量化效果。新增自然语言执行确认与方案交接测试，离线证据已重新运行生成，真实历史记录未改写。验收入口见 examples/ACCEPTANCE.md。


## 真实报价变化与超预算重规划

执行 `python scripts/evaluate_replanning.py`，使用deepseek-v4-pro、真实时钟和专用合成规则data/quote-change.json。检索展示premium参考制作费8，最终估算制作费11；预算10。模型自主选择premium后观察总额12、缺口2，改选lean，计入两次脚本费后合计8，重新估算并保存。工具结果和步骤均保留。

[输入](../examples/real-replanning/a5b646045987/input.json) · [实际输出](../examples/real-replanning/a5b646045987/output.json) · [Trace](../examples/real-replanning/a5b646045987/trace.jsonl) · [核验](../examples/real-replanning/a5b646045987/review.json)。这条是真实模型生成动作，不是Mock或强制动作回放；报价规则为本地合成测试，不代表真实供应商报价。

新增回归测试确保最终报价覆盖参考价，超预算时保存被拒绝。当前42项测试通过。所有场景集中阅读入口为 [acceptance-report.md](../examples/acceptance-report.md)。


## 正式项目题2逐项核验

| 正式要求 | 实现与证据 | 结论 |
|---|---|---|
| 主题、预算、截止时间；合成素材与费用耗时 | domain/intake及data/catalog.json | 已实现 |
| 素材检索、脚本生成、成本估算、方案保存 | tools.py四工具；业务工具为允许的本地实现 | 已实现 |
| 任务计划、步骤状态、工具结果、费用、保存或原因 | output.json中的plan/steps/estimate/status/reason | 已实现 |
| 模型观察超预算、错误等后调整，保留成功结果 | 真实12→8 Trace、真实故障恢复Trace；历史步骤保留 | 已验证 |
| 正常完成 | examples/normal及real/18d3a8f54d78/normal | 已验证 |
| 缺预算或期限 | examples/missing_budget、missing_deadline及真实追问对话 | 已验证 |
| 工具失败 | examples/tool_failure及真实tool_failure | 已验证 |
| 预算超限与无可行方案 | real-replanning/a5b646045987及examples/no_feasible | 已验证；无可行分支目前为离线证据 |
| 重复执行 | duplicate、idempotency_conflict及真实对话/repeat | 已验证 |
| 至少两条真实动态路径、Trace及执行上限 | 正常/故障/超预算真实路径，step_limit/call_limit离线测试 | 已提供 |
| 至少三组输入输出和运行记录 | examples/acceptance-report.md与原始文件 | 已提供 |
| 文档、依赖和环境模板 | README、docs五文档、pyproject.toml、.env.example | 已提供 |
| 失败步骤续跑 | 未实现终态手动续跑 | 可选加分项未完成 |

综合结论：项目题2的必需功能与验证材料已具备；不声称所有边缘分支均经过真实模型稳定性验证。未实现题1的素材审核、时段查询或发布排期，这些不属于本项目范围。实际投入约2小时，AI与个人贡献说明已填写。
