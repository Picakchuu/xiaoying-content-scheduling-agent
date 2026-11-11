"""Small conversational terminal; mandatory constraints are never guessed."""
from datetime import datetime
import json
from pathlib import Path
import uuid
from .agent import Agent
from .cli import write_result
from .domain import validate_request
from .intake import Intake, SHANGHAI, read_attachment, prepare_request
from .tools import Tools

HELP = '''内容任务规划 Agent · 对话模式
支持文件：UTF-8 .txt/.md 活动说明；.json 素材库。每个128 KiB，最多4个。
推荐输入：主题 + 预算（整数模拟单位）+ 截止日期和时刻 + 可选内容形式偏好。
例：做新品活动，预算10模拟单位，2026-12-01 18:00前完成，优先精剪视频。
主题、预算、期限缺失会追问；默认北京时间、合成素材、预算内优先满足偏好，并明确显示。
/attach 路径  附加文件（含空格路径可加引号）；/run 执行；/repeat 重放；/new 新任务；/help；/exit
理解后会展示需求摘要；输入 /run 才执行。执行完成只表示方案已保存，不代表实际制作或发布。
'''


def describe_issues(validation):
    labels = {'theme':'活动主题', 'budget':'预算（整数模拟单位）', 'deadline':'截止日期和时刻（含时区）'}
    return ', '.join([labels.get(k,k) for k in validation.missing]+validation.errors)


def chat(model, store, *, catalog, faults=None, max_steps=16, max_tool_calls=12, clock=None, read=input, emit=print):
    clock = clock or (lambda:datetime.now(SHANGHAI))
    parser = Intake(model if getattr(model,'mode',None)=='real' else None)
    emit(HELP)
    if parser.model is None:
        emit('离线模式：仅解析“预算10模拟单位”和 YYYY-MM-DD HH:MM 日期；复杂自然语言请使用真实模型。')
    request_id, history, draft, attachments, last_raw = uuid.uuid4().hex, [], {}, [], None
    while True:
        try:
            line = read('你 > ').strip()
        except (EOFError, KeyboardInterrupt):
            emit('\n已退出。未执行的需求未保存。')
            return 0
        if not line:
            continue
        if line == '/exit':
            return 0
        if line == '/help':
            emit(HELP)
            continue
        if line == '/new':
            request_id, history, draft, attachments, last_raw = uuid.uuid4().hex, [], {}, [], None
            emit('已开始新任务。')
            continue
        if line.startswith('/attach '):
            if last_raw:
                emit('任务已执行，请 /new 后附加新文件。')
                continue
            try:
                if len(attachments) >= 4:
                    raise ValueError('最多附加4个文件')
                attachment = read_attachment(line[8:].strip().strip('"').strip("'"))
                ids = [m['id'] for a in attachments+[attachment] for m in a['materials']]
                if len(set(ids)) != len(ids):
                    raise ValueError('素材ID重复，请修改文件')
                attachments.append(attachment)
                draft = {}  # Re-extract with new file context before execution.
                emit('已附加：'+attachment['name']+'；真实模式下内容将发送给所配置模型。请补充或重新描述需求以解析。')
            except (OSError, UnicodeError, ValueError):
                emit('附件读取失败：请检查路径、UTF-8编码、支持格式、文件大小和素材字段/ID。')
            continue
        if line in ('/run','/repeat'):
            if line == '/repeat' and not last_raw:
                emit('还没有执行过的任务。')
                continue
            raw = last_raw if last_raw else prepare_request(request_id,draft,attachments)
            validation = validate_request(raw, now=clock())
            if last_raw is None and (validation.missing or validation.errors):
                emit('尚不能执行。请补充：'+describe_issues(validation))
                continue
            materials = [m for a in attachments for m in a['materials']]
            tools = Tools(store,catalog,faults,materials=materials if any(a['name'].lower().endswith('.json') for a in attachments) else None)
            emit('执行中……')
            def progress(proposal, observation):
                emit('  '+proposal['action']+' · '+('成功' if observation.get('ok') else '失败：'+observation.get('error_code','unknown')))
            result = Agent(model,tools,max_steps=max_steps,max_tool_calls=max_tool_calls,clock=clock,on_event=progress).run(raw)
            folder = Path('.tmp/chat')/request_id
            write_result(result,folder/'output.json',folder/'trace.jsonl')
            last_raw = raw
            emit('状态：'+result['status']+'；费用合计：'+str(result.get('total_cost'))+'；重复重放：'+str(result.get('replayed',False)))
            if result.get('script'):
                variant=result['script']['variant']
                label=tools.catalog['variants'].get(variant,{}).get('format',variant)
                emit('内容形式：'+label+'（请核对是否符合你的偏好）')
                emit('脚本：'+result['script']['text'])
            if result.get('estimate'):
                estimate=result['estimate']
                emit('费用：已用工具 '+str(result['actual_tool_cost'])+' + 尚需制作 '+str(estimate['remaining_plan_cost'])+'；预计完成：'+estimate['estimated_finish'])
            if result.get('saved_plan_id'):
                emit('已保存方案：'+result['saved_plan_id']+'；内容制作尚未执行。')
            if result.get('reason'):
                emit('未完成原因：'+result['reason'])
            emit('结果与记录：'+str(folder.resolve())+'。/repeat 重放；/new 开始新任务。')
            continue
        if line.startswith('/'):
            emit('未知命令，请 /help 查看。')
            continue
        if last_raw:
            emit('当前任务已执行，请 /new 后描述新需求，或 /repeat 查看原结果。')
            continue
        if len(line)>8000 or sum(map(len,history))+len(line)>24000:
            emit('需求对话过长，请精简输入或 /new。')
            continue
        history.append(line)
        try:
            draft = parser.extract(history,draft,attachments,clock())
            raw = prepare_request(request_id,draft,attachments)
            validation = validate_request(raw,now=clock())
            emit('需求：'+json.dumps({k:draft[k] for k in ('theme','budget','deadline')},ensure_ascii=False))
            emit('默认：北京时间；未指定的内容形式由规划器在预算内选择；'+('使用附加JSON素材库。' if any(a['name'].lower().endswith('.json') for a in attachments) else '使用内置合成素材。'))
            if draft['uncertainties']:
                emit('待明确：'+'；'.join(draft['uncertainties']))
            if validation.missing or validation.errors:
                emit('请补充或修正：'+describe_issues(validation))
            else:
                emit('必填项已齐。可继续修改需求，或输入 /run 执行。')
        except (ValueError, RuntimeError):
            draft = {}  # Never execute stale requirements after a failed correction.
            emit('需求解析失败，尚未执行。请重新描述，或 /new 重新开始。')
