# 验证计划

当前未实现、未运行，以下均为预期，不是测试结果。

| 用例 | 场景 | 预期证据目录（待生成） |
|---|---|---|
| normal | 预算与时间充足，成功保存 | examples/normal/ |
| missing_input | 分别缺预算、缺截止时间 | examples/missing_input/ |
| tool_failure | 注入一次失败，保留前序成功结果 | examples/tool_failure/ |
| over_budget | 预算 10，初始 12，替代 8；另测无可行方案 | examples/over_budget/ |
| duplicate | 同输入重复执行及同标识不同输入 | examples/duplicate/ |
| limits | 调用上限与时间不可行 | examples/limits/ |

每组应保存 input.json、output.json、trace.jsonl，附实际执行命令、模式、模型标识和测试结果。上述文件当前不存在。

至少两条真实模型路径应展示不同工具结果引发不同后续动作，例如超预算后改选方案，以及工具失败后改用素材。Mock 与真实模型结果分别标明。

核验费用计算、步骤依赖、保存状态、幂等行为、上限终止。实现后补充实际测试命令、通过数量、失败原因和证据链接，不以预期代替实际结果。
