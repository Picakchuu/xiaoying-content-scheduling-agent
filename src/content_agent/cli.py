"""Reproducible CLI. Default is explicit offline mock execution."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import sqlite3
import sys
from .agent import Agent
from .config import load_env
from .models import MockModel, RealModel
from .storage import Store
from .tools import Tools, DEFAULT_CATALOG, TOOL_NAMES


def write_result(result, output=None, trace=None):
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text+'\n', encoding='utf-8')
    if trace:
        path = Path(trace)
        path.parent.mkdir(parents=True, exist_ok=True)
        header = {"type": "run", "request_id": result.get("request_id"), "mode": result.get("mode"),
                  "model": result.get("model"), "replayed": result.get("replayed", False),
                  "status": result["status"]}
        rows = [header] + result.get("trace", [])
        path.write_text(''.join(json.dumps(row, ensure_ascii=False)+'\n' for row in rows), encoding='utf-8')
    return text


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, help='UTF-8 JSON request file')
    parser.add_argument('--db', default='.tmp/plans.db')
    parser.add_argument('--model', choices=('mock', 'real'), default='mock')
    parser.add_argument('--env-file', help='explicit local model configuration; shell env takes precedence')
    parser.add_argument('--catalog', default=str(DEFAULT_CATALOG))
    parser.add_argument('--max-steps', type=int, default=16)
    parser.add_argument('--max-tool-calls', type=int, default=12)
    parser.add_argument('--fault', action='append', default=[], help='tool:fail_once or search_materials:partial_once')
    parser.add_argument('--now', help='timezone-aware fixed clock; mock mode only')
    parser.add_argument('--output')
    parser.add_argument('--trace')
    args = parser.parse_args(argv)
    try:
        if args.env_file:
            load_env(args.env_file)
        fixed = datetime.fromisoformat(args.now) if args.now else None
        if fixed and (args.model != 'mock' or fixed.tzinfo is None):
            raise ValueError('--now requires mock mode and a timezone-aware time')
        faults = {}
        for item in args.fault:
            key, value = item.split(':', 1)
            if key not in TOOL_NAMES:
                raise ValueError('unknown fault tool')
            faults[key] = value
        raw = json.loads(Path(args.input).read_text(encoding='utf-8-sig'))
        store = Store(args.db)
        model = MockModel() if args.model == 'mock' else RealModel()
        result = Agent(model, Tools(store, args.catalog, faults), max_steps=args.max_steps,
                       max_tool_calls=args.max_tool_calls, clock=(lambda: fixed) if fixed else None).run(raw)
        result['synthetic_clock'] = fixed.isoformat() if fixed else None
        print(write_result(result, args.output, args.trace))
        return 0 if result['status'] == 'completed' else 1
    except (OSError, ValueError, sqlite3.Error):
        # Do not echo env values, endpoint URLs or provider response bodies.
        print('Configuration, input file or storage error; check JSON, paths, model variables and execution limits.', file=sys.stderr)
        return 2
