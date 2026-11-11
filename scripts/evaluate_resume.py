"""Offline persisted failed-save recovery evidence."""
from datetime import datetime
from pathlib import Path
import json
import uuid
from content_agent.agent import Agent
from content_agent.models import MockModel
from content_agent.tools import Tools
from content_agent.storage import Store
from content_agent.cli import write_result

now=datetime.fromisoformat('2026-11-11T10:00:00+08:00')
folder=Path('examples/resume')
folder.mkdir(exist_ok=True)
raw={'request_id':'resume-demo','theme':'新品活动','budget':20,'deadline':'2026-11-12T18:00:00+08:00'}
store=Store(Path('.tmp')/('resume-'+uuid.uuid4().hex)/'runs.db')
first=Agent(MockModel(),Tools(store,faults={'save_plan':'fail_once'}),max_steps=4,clock=lambda:now).run(raw)
write_result(first,folder/'before-output.json',folder/'before-trace.jsonl')
second=Agent(MockModel(),Tools(Store(store.path)),clock=lambda:now).run(raw,resume=True)
write_result(second,folder/'output.json',folder/'trace.jsonl')
assert first['status']=='incomplete' and second['status']=='completed'
assert first['actual_tool_cost']==second['actual_tool_cost']==1
(folder/'input.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(folder/'config.json').write_text(json.dumps({'mode':'mock','fixed_now':now.isoformat(),'first_max_steps':4,'faults':{'save_plan':'fail_once'},'second_resume':True},indent=2)+'\n',encoding='utf-8')
print('Persisted resume passed: failed save retained, generation cost unchanged.')
