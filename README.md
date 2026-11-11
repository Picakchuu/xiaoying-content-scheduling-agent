# 内容任务规划 Agent

帮助运营人员在预算和截止时间内完成并保存内容活动方案。Python原生实现，支持终端对话和JSON批处理。业务工具使用合成数据，DeepSeek负责动作选择；费用为模拟单位。

## 推荐入口：对话模式

```powershell
$env:PYTHONPATH = "src"
python -m content_agent chat --model real --env-file .env
```

直接描述主题、预算和截止时间；缺少关键约束时会追问。核对中文摘要后输入“开始吧”或 `/run`。`/attach "路径"`支持UTF-8 txt/md说明和JSON素材库，每个128 KiB、最多4个；结构见data/chat-materials.example.json。真实模式会将附件内容发送给配置的模型。

`/new`新任务，`/repeat`重放，`/help`帮助，`/exit`退出。默认北京时间、合成素材和预算内的内容形式选择；不擅自补预算或期限。JSON素材库替换内置素材，txt/md仅辅助需求理解。

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

- [需求](docs/01-requirements.md)、[设计](docs/02-solution.md)、[评估与限制](docs/03-evaluation.md)
- [AI使用](docs/04-ai-usage.md)、[复盘](docs/05-retrospective.md)
- [验收索引](examples/ACCEPTANCE.md)、[测试结果](examples/test-results.txt)

方案已保存不代表内容已制作或发布。脚本和分镜采用本地模板，不声称是真实创意生成效果。个人贡献与实际投入时间须由候选人如实补充。
