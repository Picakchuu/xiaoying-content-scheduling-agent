import io
import json
import os
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from content_agent.models import RealModel, ModelError


class ModelTests(unittest.TestCase):
    def model(self):
        with patch.dict(os.environ, {"MODEL_URL": "https://example.invalid/chat/completions", "MODEL_API_KEY": "test-only", "MODEL_NAME": "fixture"}, clear=True):
            return RealModel()

    def test_request_and_content(self):
        data = {"choices": [{"message": {"content": '{"action":"estimate_cost","args":{},"why":"check"}'}}]}
        with patch('content_agent.models.urlopen', return_value=io.BytesIO(json.dumps(data).encode())) as call:
            result = self.model().decide({"state": {}})
        self.assertEqual(json.loads(result)["action"], "estimate_cost")
        self.assertEqual(json.loads(call.call_args.args[0].data)["model"], "fixture")

    def test_http_error_does_not_expose_body_or_key(self):
        with patch('content_agent.models.urlopen', side_effect=HTTPError("url", 401, "secret", {}, None)):
            with self.assertRaisesRegex(ModelError, '^model HTTP error 401$'):
                self.model().decide({})

    def test_malformed_response(self):
        with patch('content_agent.models.urlopen', return_value=io.BytesIO(b'{}')):
            with self.assertRaises(ModelError):
                self.model().decide({})

    def test_missing_config(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                RealModel()

    def test_deepseek_options_and_truncation(self):
        env = {'MODEL_URL':'https://api.deepseek.com/chat/completions', 'MODEL_API_KEY':'test-only',
               'MODEL_NAME':'deepseek-v4-pro', 'MODEL_THINKING':'disabled', 'MODEL_JSON_OUTPUT':'true', 'MODEL_MAX_TOKENS':'3000'}
        data = {'choices':[{'message':{'content':'{}'}, 'finish_reason':'length'}]}
        with patch.dict(os.environ, env, clear=True), patch('content_agent.models.urlopen', return_value=io.BytesIO(json.dumps(data).encode())) as call:
            with self.assertRaisesRegex(ModelError, 'truncated'):
                RealModel().decide({})
        body = json.loads(call.call_args.args[0].data)
        self.assertEqual(body['thinking'], {'type':'disabled'})
        self.assertEqual(body['response_format'], {'type':'json_object'})
        self.assertEqual(body['max_tokens'], 3000)
