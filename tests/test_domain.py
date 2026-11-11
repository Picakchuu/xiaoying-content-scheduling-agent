import unittest
from datetime import datetime
from content_agent.domain import validate_request

NOW = datetime.fromisoformat("2026-11-11T10:00:00+08:00")


class InputTests(unittest.TestCase):
    def data(self, **changes):
        return dict(request_id="demo", theme="新品活动", budget=10,
                    deadline="2026-11-12T10:00:00+08:00", **{}) | changes

    def test_missing_constraints(self):
        data = self.data()
        del data["budget"]
        del data["deadline"]
        result = validate_request(data, now=NOW)
        self.assertEqual(result.missing, ["budget", "deadline"])
        self.assertIsNone(result.request)

    def test_invalid_budget(self):
        for value in (True, -1, 1.5, "10"):
            with self.subTest(value=value):
                self.assertIsNone(validate_request(self.data(budget=value), now=NOW).request)

    def test_deadline_requires_future_and_timezone(self):
        for value in ("2026-11-12T10:00:00", "2026-11-11T10:00:00+08:00", "invalid"):
            with self.subTest(value=value):
                self.assertIsNone(validate_request(self.data(deadline=value), now=NOW).request)

    def test_equivalent_deadlines_have_same_fingerprint(self):
        a = validate_request(self.data(), now=NOW).request
        b = validate_request(self.data(deadline="2026-11-12T02:00:00+00:00"), now=NOW).request
        self.assertEqual(a.fingerprint(), b.fingerprint())
        c = validate_request(self.data(budget=8), now=NOW).request
        self.assertNotEqual(a.fingerprint(), c.fingerprint())

    def test_zero_budget_is_valid(self):
        self.assertIsNotNone(validate_request(self.data(budget=0), now=NOW).request)

    def test_invalid_root_and_blank_theme(self):
        self.assertTrue(validate_request([], now=NOW).errors)
        self.assertTrue(validate_request(self.data(theme="  "), now=NOW).errors)
