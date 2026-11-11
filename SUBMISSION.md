# 提交信息

- 项目：项目题 2：内容任务规划 Agent。
- GitHub：https://github.com/Picakchuu/xiaoying-content-scheduling-agent
- 最终commit SHA：使用 `git rev-parse HEAD` 获取本次提交完整值，与提交表单保持一致。
- 实际投入：约2个半小时。
- 个人贡献：主要需求和设计决策、代码审核修改、CLI实际试用与反馈；以AI辅助编码为主，代码/测试/文档大部分初稿由AI协助完成。

## 评审顺序

1. README.md：环境与运行、模型和Mock边界、数据库说明。
2. examples/acceptance-report.md：集中输入、实际输出摘要和关键Trace。
3. docs/03-evaluation.md：验收覆盖、真实模型验证与已知限制。
4. docs/04-ai-usage.md与docs/05-retrospective.md：AI工作范围、个人贡献和复盘。

运行：仓库根目录设置PYTHONPATH=src，执行 `python -m unittest discover -s tests -v`；离线演示与真实交互命令见README。

原始运行证据全部保留；.env、数据库、缓存与临时个人试用记录均不纳入Git交付。
