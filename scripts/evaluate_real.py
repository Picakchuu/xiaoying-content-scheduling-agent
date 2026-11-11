"""Execute three live model paths, preserve results even if expectations fail."""
import argparse
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', default='.env')
    args = parser.parse_args()
    load_env(args.env_file)
    model = RealModel()
    run_id = uuid.uuid4().hex[:12]
    folder = Path('examples/real')/run_id
    store = Store(Path('.tmp')/('real-'+run_id)/'runs.db')
    summary = []
    for case, budget, faults in [('normal',20,{}), ('over_budget',10,{}), ('tool_failure',10,{'generate_script':'fail_once'})]:
        now = datetime.now(timezone.utc)
        raw = {'request_id':f'{run_id}-{case}', 'theme':'新品活动，优先考虑精剪视频效果', 'budget':budget,
               'deadline':(now+timedelta(days=1)).isoformat()}
        target = folder/case
        target.mkdir(parents=True, exist_ok=True)
        (target/'input.json').write_text(json.dumps(raw, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        output = Agent(model, Tools(store, faults=faults)).run(raw)
        write_result(output, target/'output.json', target/'trace.jsonl')
        (target/'config.json').write_text(json.dumps({'mode':'real', 'model':model.name, 'faults':faults, 'started_at':now.isoformat(),
             'max_steps':16, 'max_tool_calls':12}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        summary.append({'case':case, 'status':output['status'], 'reason':output.get('reason')})
        print(case, output['status'])
    (folder/'summary.json').write_text(json.dumps({'model':model.name, 'results':summary}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('Evidence:', folder)
    print('Review actual actions: a model may choose a cheap plan upfront rather than experience a budget rejection.')


if __name__ == '__main__':
    main()
