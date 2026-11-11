from contextlib import redirect_stdout, redirect_stderr
import io
import json
import unittest
from content_agent.cli import main
from support import temporary_workspace


class CliTests(unittest.TestCase):
    def setUp(self):
        self.root = temporary_workspace(self)
        self.input = self.root/'input.json'
        self.input.write_text(json.dumps({'request_id':'cli', 'theme':'新品活动', 'budget':10,
                              'deadline':'2026-11-12T10:00:00+08:00'}), encoding='utf-8')

    def invoke(self, extra=()):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return main(['--input', str(self.input), '--db', str(self.root/'runs.db'),
                         '--now', '2026-11-11T10:00:00+08:00', *extra])

    def test_cli_artifacts_and_repeat(self):
        output, trace = self.root/'output.json', self.root/'trace.jsonl'
        self.assertEqual(self.invoke(['--output', str(output), '--trace', str(trace)]), 0)
        result = json.loads(output.read_text(encoding='utf-8'))
        self.assertEqual(result['estimate']['total_cost'], 8)
        self.assertGreater(len(trace.read_text(encoding='utf-8').splitlines()), 1)
        self.assertEqual(self.invoke(), 0)

    def test_config_error(self):
        self.assertEqual(self.invoke(['--max-steps', '0']), 2)

    def test_incomplete_exit_code(self):
        self.assertEqual(self.invoke(['--max-steps', '1']), 1)
