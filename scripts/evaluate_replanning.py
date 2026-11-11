"""Live model observes final quote exceeding preliminary material-table price."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import uuid
from content_agent.agent import Agent
from content_agent.cli import write_result
from content_agent.config import load_env
from content_agent.models import RealModel
from content_agent.storage import Store
from content_agent.tools import Tools


def main():
    load_env('.env')
    model=RealModel()
    folder=Path('examples/real-replanning')/uuid.uuid4().hex[:12]
    folder.mkdir(parents=True)
    raw={'request_id':folder.name,'theme':'新品活动，预算允许时优先精剪视频，超预算可降低制作规格',
         'budget':10,'deadline':(datetime.now(timezone.utc)+timedelta(days=1)).isoformat()}
    store=Store(Path('.tmp')/('replanning-'+folder.name)/'runs.db')
    output=Agent(model,Tools(store,'data/quote-change.json')).run(raw)
    (folder/'input.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    write_result(output,folder/'output.json',folder/'trace.jsonl')
    estimates=[s['observation']['data'] for s in output['trace'] if s['action']=='estimate_cost' and s['observation']['ok']]
    checks={'completed':output['status']=='completed',
            'over_budget_observed':any(e['budget_gap']>0 for e in estimates),
            'reestimated_within_budget':len(estimates)>1 and estimates[-1]['feasible'],
            'costs':[e['total_cost'] for e in estimates]}
    (folder/'config.json').write_text(json.dumps({'mode':'real','model':model.name,'catalog':'data/quote-change.json',
        'scenario':'参考premium制作费8，最终报价11；两次脚本生成后lean合计8。工具不强制模型选premium。'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (folder/'review.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')
    print(folder,checks,flush=True)
    if not all(checks[k] for k in ('completed','over_budget_observed','reestimated_within_budget')):
        raise SystemExit(1)


if __name__=='__main__':
    main()
