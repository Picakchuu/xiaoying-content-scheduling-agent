# 分步开发流程

每一步新建分支，修改和删除也在该步分支内进行；验证、提交后再合并。main 保留可验证版本。未经完成验证，不将开发中功能描述为已完成。

| 步骤 | 分支 | 范围 |
|---|---|---|
| 1 | feat/01-domain-contracts | Python 包、输入校验、状态契约和基础测试 |
| 2 | feat/02-tools-storage | 合成数据、四个工具、费用/耗时、SQLite 幂等保存、故障注入 |
| 3 | feat/03-react-loop | 动作校验、模型接口、真实模型与 Mock、Trace、有限循环 |
| 4 | feat/04-cli-evaluation | CLI、场景测试、实际运行证据与交付文档 |

默认先验证并提交各步；推送允许在本次授权范围内执行。合并可采用本地经测试的快进，或 GitHub PR；遇到冲突、远程已有改动或需要登录时先说明情况。

## 复用检查

已只读检查相邻 xiaoying-knowledge-qa-agent 的 actions.py、trace.py、llm.py、agent.py、依赖与环境变量模板。

可借鉴：decide(context) 模型接口、动作白名单校验、观察回灌、双上限、逐步 Trace。当前未复制源码。

不直接复用：问答动作枚举、引用校验器、同义词、文档冲突规则、问答 Mock。Trace 依赖问答工具摘要，需重新定义通用观察结构；模型适配文件也混合了业务 Prompt 和 Mock，后续应拆分。未读取或复制 .env。

## 第一步验证

PowerShell：

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

测试使用固定当前时间，避免时间推进使测试失效。当前只测试领域输入契约，不证明 Agent 或模型效果。业务入口尚未实现。
