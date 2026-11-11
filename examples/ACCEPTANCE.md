# 验收索引

执行：设置PYTHONPATH=src后运行 `python scripts/make_examples.py`。每个离线目录包含input.json、output.json、trace.jsonl、config.json。

| 验收点 | 证据目录 | 检查内容 |
|---|---|---|
| 正常完成 | normal/ | 保存成功、依赖和费用 |
| 缺预算/期限 | missing_budget/、missing_deadline/ | needs_input，不执行工具 |
| 工具失败 | tool_failure/ | 失败状态保留、前序成功保留 |
| 超预算 | over_budget/、no_feasible/ | 12→8及无可行方案缺口 |
| 重复执行 | duplicate/、idempotency_conflict/ | 不重复保存、不同输入冲突 |
| 部分成功 | partial_success/ | 基于部分素材调整方案 |
| 执行上限 | call_limit/、step_limit/ | incomplete和保留结果 |
| 时间约束 | time_replan/、time_infeasible/ | 替代及不可行 |
| 真实决策 | real/18d3a8f54d78/ | 正常、预算规避、模型主动故障重试 |
| 对话与文件 | chat-live/7ac3833462c8/ | 追问、相对日期、素材输入及重放 |

离线12→8不作为真实模型证明；真实报价变化样本 real-replanning/a5b646045987/ 已另行验证12→8。早期预算样本是提前规避，不能混为同一次执行。集中阅读见 [acceptance-report.md](acceptance-report.md)。

提交仓库：https://github.com/Picakchuu/xiaoying-content-scheduling-agent

最终SHA：提交时运行 `git rev-parse HEAD` 获取，避免文档中的SHA自引用失效。题号请按正式试卷核对；本仓库项目名称为“内容任务规划 Agent”。实际投入约2小时，个人贡献详见docs/04-ai-usage.md。
