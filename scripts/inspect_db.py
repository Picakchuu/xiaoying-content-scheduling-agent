"""Read-only database overview; does not modify or create a database."""
import argparse
import json
from pathlib import Path
import sqlite3
from contextlib import closing

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--db',default='.tmp/plans.db')
args=parser.parse_args()
with closing(sqlite3.connect(Path(args.db).resolve().as_uri()+'?mode=ro',uri=True)) as conn:
    for request_id, raw in conn.execute('SELECT id,state FROM runs'):
        state=json.loads(raw)
        print(json.dumps({'request_id':request_id,'status':state['status'],'tool_cost':state['actual_tool_cost'],
                          'saved_plan_id':state['saved_plan_id'],'steps':len(state['steps'])},ensure_ascii=False))
