# 内容任务规划 Agent

小影校招 AI Agent 岗 · 内容任务规划 Agent（ReAct 决策 + 预算与时限约束 + 动态重规划）。

帮助运营人员从主题、预算和截止时间生成并保存内容活动方案。采用 Python 原生单 Agent，提供 CLI、四个本地业务工具、SQLite 幂等存储、模型动作校验和执行上限。

**当前验证状态：31 项测试、14 组离线运行记录通过；DeepSeek V4 Pro 的3组真实调用均成功保存方案。真实记录覆盖正常、预算规避和模型自主故障重试；真实超预算后改选方案尚未覆盖。离线 Mock 仅证明流程。**

## 环境与安装

Python 3.11+，运行和测试仅依赖标准库。以下命令在仓库根目录的 PowerShell 执行：

```powershell
$env:PYTHONPATH = "src"
python -m content_agent --help
python -m unittest discover -s tests -v
```

也可执行 `python -m pip install -e .` 安装为可编辑包。当前运行方式面向源码 checkout / 可编辑安装，合成数据从仓库 `data/catalog.json` 读取，不提供独立 wheel 分发。

## 离线运行

```powershell
$env:PYTHONPATH = "src"
python -m content_agent --model mock --input examples/over_budget/input.json --now "2026-11-11T10:00:00+08:00" --db .tmp/demo.db --output .tmp/output.json --trace .tmp/trace.jsonl
```

第一次执行：premium 估算 12，超过预算 10；改选 lean 后累计两次生成费用，估算 8；重新估算后保存成功。再次执行相同命令返回保存结果，`replayed=true`，不重新执行工具。

`--now` 仅用于 Mock 的固定时间复现。日常新输入去掉该参数，并填写真实的未来截止时间。相同 request_id 对应不同主题、预算或截止时间会报幂等冲突；尝试新方案请使用新 request_id。

故障演示（使用独立数据库，避免命中已保存结果）：

```powershell
python -m content_agent --input examples/tool_failure/input.json --now "2026-11-11T10:00:00+08:00" --fault generate_script:fail_once --db .tmp/failure.db --output .tmp/failure-output.json --trace .tmp/failure-trace.jsonl
```

支持 `search_materials:partial_once`；其他工具支持 `fail_once`。注入发生在执行前，不收费。正常生成脚本每次收费 1 单位。默认模型轮次上限 16、工具调用上限 12；`--max-steps`、`--max-tool-calls` 可调整。终态为 completed 时退出码 0，needs_input / incomplete / failed 为 1，输入文件、配置或存储错误为 2。

## 输入与结果

```json
{
  "request_id": "campaign-001",
  "theme": "新品活动",
  "budget": 10,
  "deadline": "2026-12-01T18:00:00+08:00"
}
```

预算为非负整数模拟单位；截止时间必须包含时区。结果包含当前脚本、步骤实际状态、工具结果、估算总费用、实际工具费用、已保存计划及 Trace；未完成时给出原因和可用估算中的缺口。`completed` 表示方案已保存，内容制作仍是计划中的 pending 任务，不代表已制作或发布内容。

## 真实模型接入

使用支持 chat-completions 消息格式的服务，环境变量模板见 `.env.example`。可在当前终端设置环境变量，或使用 `--env-file .env` 显式读取本地配置（终端环境变量优先）：

```powershell
$env:MODEL_URL = "https://api.deepseek.com/chat/completions"
$env:MODEL_NAME = "deepseek-v4-pro"
# 在本地终端设置 MODEL_API_KEY；不要提交密钥。
python -m content_agent --model real --input .tmp/real-input.json --db .tmp/real.db --output .tmp/real-output.json --trace .tmp/real-trace.jsonl
```

先按上面的输入格式创建 `.tmp/real-input.json`，使用未来期限和新的 request_id。真实模式不允许 `--now`。真实模型与 Mock 共用执行器与工具，模型只能提出动作，预算、依赖和完成状态由代码校验。模型 API 的真实账单不计入题目模拟预算，需自行管理。

## 评审入口

- [需求与验收](docs/01-requirements.md)、[架构与取舍](docs/02-solution.md)
- [评估结果与限制](docs/03-evaluation.md)、[离线结果汇总](examples/summary.json)、[测试输出](examples/test-results.txt)
- [AI 使用说明](docs/04-ai-usage.md)、[复盘](docs/05-retrospective.md)、[分支开发流程](docs/06-development.md)
- [超预算 Trace](examples/over_budget/trace.jsonl)、[工具失败 Trace](examples/tool_failure/trace.jsonl)

重新生成全部离线证据：`python scripts/make_examples.py`。使用独立临时数据库，写入真实执行输出并运行测试；不会生成真实模型证据。各目录 config.json 标明故障、上限与固定时钟。重复与冲突用例依赖 normal 的相同数据库，由脚本按顺序执行。

本项目未扩展 UI、HTTP API、多 Agent 或真实发布。历史 `PROJECT_PLAN.md` 是素材审核/发布排期方向的早期文件，不是当前实现规格，以 docs/01-requirements.md 为准。


## DeepSeek V4 Pro 验证入口

当前选择模型为 `deepseek-v4-pro`，官方端点为 `https://api.deepseek.com/chat/completions`。复制 `.env.example` 为本地 `.env`（如果已有配置请保留），只在本地填写密钥。模板设置 `MODEL_THINKING=disabled`、`MODEL_JSON_OUTPUT=true` 与 `MODEL_MAX_TOKENS=3000`；模型根据观察选择动作不要求开启思考模式，且程序不保存 reasoning_content。

```powershell
$env:PYTHONPATH = "src"
python scripts/evaluate_real.py --env-file .env
```

该命令会实际调用模型服务，运行正常、预算约束、工具失败三个场景，证据写入 `examples/real/<运行标识>/`。不要把失败记录改写为成功；模型可能预先选择廉价方案，仍需人工核对是否已覆盖两条观察后调整路径。已执行3组真实验证，结果与边界见 [真实验证汇总](examples/real/18d3a8f54d78/review.json)。

单独调用可使用 `python -m content_agent --model real --env-file .env --input .tmp/real-input.json --db .tmp/real.db`。DeepSeek参数依据：[官方Chat Completions文档](https://api-docs.deepseek.com/api/create-chat-completion/)。
