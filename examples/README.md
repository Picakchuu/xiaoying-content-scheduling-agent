# 实际运行证据

执行 `python scripts/make_examples.py` 重新生成14组离线实际输入/输出/Trace及测试结果。每组config.json标明固定时钟、故障注入、执行上限及预期/实际状态。

所有当前证据为mock，真实模型尚未验证。重复/冲突用例在normal之后使用同一数据库执行；duplicate的Trace是原执行的重放，并非第二次工具执行。
