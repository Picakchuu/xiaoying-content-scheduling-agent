"""Run an actual multi-turn intake + attachment + planning interaction."""
from datetime import datetime
import json
from pathlib import Path
import shutil
import uuid
from content_agent.chat import chat
from content_agent.config import load_env
from content_agent.intake import SHANGHAI
from content_agent.models import RealModel
from content_agent.storage import Store
from content_agent.tools import DEFAULT_CATALOG


def main():
    load_env('.env')
    model=RealModel()
    run_id=uuid.uuid4().hex[:12]
    folder=Path('examples/chat-live')/run_id
    folder.mkdir(parents=True)
    transcript=[]
    inputs=iter(['/attach data/chat-materials.example.json','做新品推广，优先短视频','/run',
                 '预算10模拟单位，明天下午6点前完成','/run','/repeat','/exit'])
    def read(prompt):
        text=next(inputs)
        transcript.append({'role':'user','text':text})
        return text
    def emit(text):
        transcript.append({'role':'assistant','text':text})
        print(text,flush=True)
    started=datetime.now(SHANGHAI).isoformat()
    store=Store(Path('.tmp')/('chat-evaluation-'+run_id)/'runs.db')
    chat(model,store,catalog=DEFAULT_CATALOG,read=read,emit=emit)
    with store.connect() as conn:
        rows=conn.execute('SELECT id FROM runs').fetchall()
    state=store.read(rows[0][0])
    source=Path('.tmp/chat')/state['request_id']
    for name in ('output.json','trace.jsonl'):
        shutil.copyfile(source/name,folder/name)
    (folder/'conversation.json').write_text(json.dumps({'mode':'real','model':model.name,'started_at':started,'messages':transcript},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    checks={'only_one_request':len(rows)==1, 'completed':state['status']=='completed',
            'uses_attached_source':bool(state['script'] and state['script']['sources'][0]['id']=='local-product'),
            'short_video_preference_met':bool(state['script'] and state['script']['variant']=='lean')}
    (folder/'review.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')
    print('Evidence:',folder)
    if not all(checks.values()):
        raise SystemExit('One or more checks failed; actual evidence preserved.')


if __name__=='__main__':
    main()
