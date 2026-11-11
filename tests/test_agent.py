from datetime import timedelta
import unittest
from content_agent.agent import Agent
from content_agent.models import MockModel, action
from content_agent.storage import Store
from content_agent.tools import Tools
from support import temporary_workspace
from test_tools_storage import NOW


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(temporary_workspace(self)/"runs.db")

    def run_case(self, budget=10, faults=None, model=None, **limits):
        return Agent(model or MockModel(), Tools(self.store, faults=faults), clock=lambda: NOW, **limits).run(
            {"request_id": "run", "theme": "新品活动", "budget": budget, "deadline": (NOW+timedelta(days=1)).isoformat()})

    def test_normal_and_duplicate(self):
        out = self.run_case(budget=20)
        self.assertEqual(out["status"], "completed")
        self.assertEqual(out["estimate"]["total_cost"], 12)
        duplicate = self.run_case(budget=20)
        self.assertTrue(duplicate["replayed"])
        self.assertEqual(out["steps"], duplicate["steps"])

    def test_replan(self):
        out = self.run_case()
        self.assertEqual(out["status"], "completed")
        self.assertEqual(out["estimate"]["total_cost"], 8)
        estimates = [r for r in out["trace"] if r["action"] == "estimate_cost"]
        self.assertEqual(estimates[0]["next_action"], "generate_script")
        self.assertEqual(estimates[1]["next_action"], "save_plan")

    def test_tool_failure(self):
        out = self.run_case(faults={"generate_script": "fail_once"})
        self.assertEqual(out["status"], "completed")
        self.assertEqual(out["steps"][0]["status"], "succeeded")
        self.assertEqual(out["steps"][1]["status"], "failed")
        self.assertEqual(out["script"]["variant"], "lean")

    def test_no_feasible_plan(self):
        out = self.run_case(budget=2)
        self.assertEqual(out["status"], "incomplete")
        self.assertIsNone(out["saved_plan_id"])

    def test_tool_limit(self):
        out = self.run_case(max_tool_calls=1)
        self.assertEqual(len(out["steps"]), 1)
        self.assertEqual(out["reason"], "tool_call_limit reached")

    def test_invalid_model_outputs_are_bounded(self):
        class Bad:
            name = "bad-fixture"
            def decide(self, ctx):
                return action("finish", {"reason": "fake", "status": "completed"}, "invalid")
        out = self.run_case(model=Bad(), max_steps=3)
        self.assertEqual(out["reason"], "step_limit reached")
        self.assertEqual(len(out["trace"]), 3)
        self.assertFalse(out["steps"])

    def test_partial(self):
        out = self.run_case(faults={"search_materials": "partial_once"})
        self.assertEqual(out["status"], "completed")
        self.assertEqual(out["script"]["variant"], "lean")

    def test_saved_result_replayed_after_deadline(self):
        self.run_case(budget=20)
        agent = Agent(MockModel(), Tools(self.store), clock=lambda: NOW+timedelta(days=2))
        out = agent.run({"request_id":"run", "theme":"新品活动", "budget":20,
                         "deadline":(NOW+timedelta(days=1)).isoformat()})
        self.assertEqual(out["status"], "completed")
        self.assertTrue(out["replayed"])

    def test_unknown_provider_failure_is_bounded_and_redacted(self):
        class Broken:
            name = "broken-fixture"
            def decide(self, ctx):
                raise RuntimeError("secret-provider-details")
        out = self.run_case(model=Broken(), max_steps=2)
        self.assertEqual(out["status"], "incomplete")
        self.assertNotIn("secret-provider-details", str(out))

    def test_clock_rechecked_after_model_latency(self):
        current=[NOW]
        class SlowModel:
            name='slow-fixture'
            def decide(self,ctx):
                current[0]=NOW+timedelta(days=2)
                return action('search_materials',{'query':'新品'},'search')
        out=Agent(SlowModel(),Tools(self.store),clock=lambda:current[0],max_steps=1).run({
            'request_id':'slow','theme':'新品','budget':10,'deadline':(NOW+timedelta(days=1)).isoformat()})
        self.assertEqual(out['steps'][0]['error'],'deadline_exceeded')

    def test_resume_failed_save_reuses_script_and_cost(self):
        raw={'request_id':'resume','theme':'新品活动','budget':20,'deadline':(NOW+timedelta(days=1)).isoformat()}
        tools=Tools(self.store,faults={'save_plan':'fail_once'})
        first=Agent(MockModel(),tools,clock=lambda:NOW,max_steps=4).run(raw)
        self.assertEqual(first['status'],'incomplete')
        self.assertEqual(first['steps'][-1]['status'],'failed')
        second=Agent(MockModel(),Tools(self.store),clock=lambda:NOW).run(raw,resume=True)
        self.assertEqual(second['status'],'completed')
        self.assertEqual(second['actual_tool_cost'],1)
        self.assertEqual(second['resume_count'],1)
        self.assertEqual([s['tool'] for s in second['steps']].count('generate_script'),1)
        self.assertEqual(second['steps'][-2]['status'],'failed')
        repeated=Agent(MockModel(),Tools(self.store),clock=lambda:NOW).run(raw,resume=True)
        self.assertTrue(repeated['replayed'])
        self.assertEqual(second['steps'],repeated['steps'])

    def test_resume_limit_and_expiry(self):
        raw={'request_id':'limits','theme':'新品活动','budget':2,'deadline':(NOW+timedelta(days=1)).isoformat()}
        agent=Agent(MockModel(),Tools(self.store),clock=lambda:NOW,max_steps=1)
        agent.run(raw)
        for _ in range(3): agent.run(raw,resume=True)
        self.assertIn('resume_limit',agent.run(raw,resume=True)['resume_error'])
        late=Agent(MockModel(),Tools(self.store),clock=lambda:NOW+timedelta(days=2))
        self.assertIn('deadline',late.run(raw,resume=True)['resume_error'])

    def test_resume_does_not_reset_tool_limit(self):
        raw={'request_id':'cap','theme':'新品活动','budget':20,'deadline':(NOW+timedelta(days=1)).isoformat()}
        agent=Agent(MockModel(),Tools(self.store),clock=lambda:NOW,max_tool_calls=1)
        agent.run(raw)
        self.assertIn('tool_call_limit',agent.run(raw,resume=True)['resume_error'])
