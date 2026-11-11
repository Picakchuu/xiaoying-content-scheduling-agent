"""Execute reproducible offline acceptance cases; never fabricate model evidence."""
from datetime import datetime
import io
import json
from pathlib import Path
import unittest
import uuid
from content_agent.agent import Agent
from content_agent.cli import write_result
from content_agent.models import MockModel
from content_agent.storage import Store
from content_agent.tools import Tools

NOW = datetime.fromisoformat('2026-11-11T10:00:00+08:00')
BASE = dict(theme='新品活动', budget=20, deadline='2026-11-12T10:00:00+08:00')
CASES = [
    ('normal', BASE, {}, {}, 'completed'),
    ('missing_budget', {k:v for k,v in BASE.items() if k != 'budget'}, {}, {}, 'needs_input'),
    ('missing_deadline', {k:v for k,v in BASE.items() if k != 'deadline'}, {}, {}, 'needs_input'),
    ('tool_failure', BASE, {'generate_script':'fail_once'}, {}, 'completed'),
    ('over_budget', BASE | {'budget':10}, {}, {}, 'completed'),
    ('no_feasible', BASE | {'budget':2}, {}, {}, 'incomplete'),
    ('partial_success', BASE, {'search_materials':'partial_once'}, {}, 'completed'),
    ('time_replan', BASE | {'deadline':'2026-11-11T11:00:00+08:00'}, {}, {}, 'completed'),
    ('time_infeasible', BASE | {'deadline':'2026-11-11T10:10:00+08:00'}, {}, {}, 'incomplete'),
    ('no_materials', BASE | {'theme':'火星基地'}, {}, {}, 'incomplete'),
    ('call_limit', BASE, {}, {'max_tool_calls':1}, 'incomplete'),
    ('step_limit', BASE, {}, {'max_steps':1}, 'incomplete'),
    ('duplicate', BASE, {}, {}, 'completed'),
    ('idempotency_conflict', BASE | {'budget':9}, {}, {}, 'failed'),
]


def main():
    store = Store(Path('.tmp')/('examples-'+uuid.uuid4().hex)/'runs.db')
    summary = []
    for name, fields, faults, limits, expected in CASES:
        request_id = 'normal' if name in ('duplicate', 'idempotency_conflict') else name
        raw = {'request_id':request_id, **fields}
        folder = Path('examples')/name
        folder.mkdir(parents=True, exist_ok=True)
        (folder/'input.json').write_text(json.dumps(raw, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        output = Agent(MockModel(), Tools(store, faults=faults), clock=lambda:NOW, **limits).run(raw)
        output['synthetic_clock'] = NOW.isoformat()
        write_result(output, folder/'output.json', folder/'trace.jsonl')
        assert output['status'] == expected, (name, output['status'])
        if name == 'duplicate':
            assert output['replayed']
        if name == 'over_budget':
            assert output['estimate']['total_cost'] == 8
        config = {'mode':'mock', 'fixed_now':NOW.isoformat(), 'faults':faults, 'limits':limits,
                  'expected_status':expected, 'actual_status':output['status']}
        (folder/'config.json').write_text(json.dumps(config, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        summary.append({'case':name, 'expected':expected, 'actual':output['status'], 'passed':True})
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.discover('tests')
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    Path('examples/test-results.txt').write_text(stream.getvalue(), encoding='utf-8')
    Path('examples/summary.json').write_text(json.dumps({'mode':'mock', 'real_model_evaluated':False,
        'cases':summary, 'tests_run':result.testsRun, 'tests_passed':result.wasSuccessful()}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(f'{len(summary)} offline cases and {result.testsRun} tests passed; real model not evaluated.')


if __name__ == '__main__':
    main()
