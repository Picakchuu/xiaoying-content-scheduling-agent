import sqlite3
from contextlib import closing
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from content_agent.domain import Request
from content_agent.storage import Store, ConflictError
from content_agent.tools import Tools
from support import temporary_workspace

NOW = datetime.fromisoformat("2026-11-11T10:00:00+08:00")


class ToolsTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(temporary_workspace(self)/"state.db")
        self.request = Request("case", "新品活动", 10, NOW+timedelta(days=1))
        self.store.start(self.request)
        self.tools = Tools(self.store)

    def call(self, name, **args):
        return self.tools.execute("case", name, args, now=NOW)

    def script(self, variant="premium"):
        self.call("search_materials", query="新品")
        return self.call("generate_script", variant=variant, material_ids=["brand"])

    def test_replan_counts_sunk_cost_and_saves(self):
        self.script()
        self.assertEqual(self.call("estimate_cost")["data"]["total_cost"], 12)
        self.assertEqual(self.call("save_plan")["error_code"], "budget_exceeded")
        self.call("generate_script", variant="lean", material_ids=["brand"])
        self.assertEqual(self.call("save_plan")["error_code"], "dependency_missing")
        self.assertEqual(self.call("estimate_cost")["data"]["total_cost"], 8)
        self.assertTrue(self.call("save_plan")["ok"])
        state = self.store.read("case")
        self.assertEqual(state["status"], "completed")
        self.assertEqual(len([s for s in state["steps"] if s["tool"] == "generate_script"]), 2)

    def test_failure_keeps_success_and_no_charge(self):
        self.call("search_materials", query="新品")
        self.tools = Tools(self.store, faults={"generate_script": "fail_once"})
        self.assertFalse(self.call("generate_script", variant="lean", material_ids=["brand"])["ok"])
        state = self.store.read("case")
        self.assertEqual(state["actual_tool_cost"], 0)
        self.assertEqual(state["steps"][0]["status"], "succeeded")
        self.assertTrue(self.call("generate_script", variant="lean", material_ids=["brand"])["ok"])

    def test_duplicate_and_conflict(self):
        self.script("lean")
        self.call("estimate_cost")
        self.call("save_plan")
        self.assertTrue(self.store.start(self.request)[1])
        with self.assertRaises(ConflictError):
            self.store.start(Request("case", "other", 10, self.request.deadline))
        self.assertEqual(self.call("save_plan")["error_code"], "terminal_state")
        with closing(sqlite3.connect(self.store.path)) as conn:
            self.assertEqual(conn.execute("SELECT count(*) FROM plans").fetchone()[0], 1)

    def test_save_rechecks_time(self):
        self.script("lean")
        self.call("estimate_cost")
        result = self.tools.execute("case", "save_plan", {}, now=self.request.deadline-timedelta(minutes=5))
        self.assertEqual(result["error_code"], "deadline_exceeded")
        self.assertIsNone(self.store.read("case")["saved_plan_id"])

    def test_partial_search(self):
        self.tools = Tools(self.store, faults={"search_materials": "partial_once"})
        result = self.call("search_materials", query="活动")
        self.assertTrue(result["data"]["partial"])
        self.assertEqual(len(result["data"]["materials"]), 1)

    def test_stale_revision_and_dependency(self):
        self.assertEqual(self.call("estimate_cost")["error_code"], "dependency_missing")
        result = self.tools.execute("case", "search_materials", {"query": "新品"}, now=NOW, expected_revision=0)
        self.assertEqual(result["error_code"], "stale_state")

    def test_final_quote_overrides_reference_and_blocks_save(self):
        self.tools=Tools(self.store,'data/quote-change.json')
        search=self.call('search_materials',query='新品')
        self.assertEqual(search['data']['variants']['premium']['production_cost'],8)
        self.call('generate_script',variant='premium',material_ids=['brand'])
        self.assertEqual(self.call('estimate_cost')['data']['total_cost'],12)
        self.assertEqual(self.call('save_plan')['error_code'],'budget_exceeded')
        self.assertIsNone(self.store.read('case')['saved_plan_id'])
