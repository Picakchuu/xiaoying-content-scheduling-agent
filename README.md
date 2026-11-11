# 内容任务规划 Agent

帮助运营人员在预算和截止时间内完成并保存内容活动方案。Python原生实现，支持终端对话和JSON批处理。业务工具使用合成数据，DeepSeek负责动作选择；费用为模拟单位。

## 目录

- src/content_agent/：领域校验、模型、工具、存储和CLI。
- tests/：标准库unittest可执行测试。
- data/：合成素材、参考/最终报价规则和附件样例。
- examples/：集中验收报告、离线及真实输入/输出/Trace、测试结果。
- scripts/：证据生成、真实评估和数据库只读检查。
- docs/：需求、设计、评估、AI使用与复盘。

## 推荐入口：对话模式

先在仓库根目录执行以下命令，仅在.env不存在时复制模板，然后在本地填写MODEL_API_KEY：

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```


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

方案已保存不代表内容已制作或发布。脚本和分镜采用本地模板。实际投入约2个半小时，以AI辅助编码为主；个人承担主要需求/设计决策、代码审核修改和CLI试用，详见AI使用说明。


## 数据库

使用Python标准库sqlite3访问SQLite，无需安装数据库服务。默认文件为仓库下 `.tmp/plans.db`，可用 `--db 路径` 指定。`runs(id,fingerprint,state)`保存请求身份和JSON执行快照；`plans(request_id,plan_id,payload)`保存方案，request_id唯一，防止重复保存。

状态和方案在事务中提交，失败回滚；连接用后关闭。适用于本地单执行者CLI，不是生产级并发调度。数据库和临时输出不会提交Git。

```powershell
python scripts/inspect_db.py --db .tmp/plans.db
```

该命令只读列出请求编号、状态、费用和保存ID，不创建数据库。更换数据库文件会失去原库的幂等历史；勿在任务运行时删除数据库。

## 集中验收

[一份完整验收报告](examples/acceptance-report.md)集中列出输入、实际输出摘要和逐步Trace；原始文件通过链接保留。离线重建后运行 `python scripts/build_acceptance_report.py` 更新报告。

真实超预算后重规划已验证：[12→8实际记录](examples/real-replanning/a5b646045987/review.json)。复现命令为 `python scripts/evaluate_replanning.py`，会真实调用模型；场景是参考价与最终报价不同，不预设模型动作。


## 手动续跑

当前对话任务未完成时输入 `/resume`。跨进程可使用原JSON输入与原数据库：

```powershell
python -m content_agent --model real --env-file .env --input 原输入.json --db 原数据库.db --resume
```

续跑保留成功结果、失败历史和已花费用，由原模型重新选择下一步；成功任务仅重放。每个请求最多3次手动续跑，累计工具调用上限不重置。原输入、模型和模式必须一致，过期或预算不足不会因续跑被绕过。相同故障注入的已使用标记不会清零。

离线验证：`python scripts/evaluate_resume.py`，证据见examples/resume。投入时间约2个半小时。
