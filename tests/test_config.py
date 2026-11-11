import os
import unittest
from unittest.mock import patch
from content_agent.config import load_env
from support import temporary_workspace


class ConfigTests(unittest.TestCase):
    def test_literal_values_and_shell_precedence(self):
        file = temporary_workspace(self)/'local.env'
        file.write_text('# comment\nMODEL_NAME="deepseek-v4-pro"\nMODEL_API_KEY=literal-$TOKEN\n', encoding='utf-8')
        with patch.dict(os.environ, {'MODEL_NAME':'shell-value'}, clear=True):
            load_env(file)
            self.assertEqual(os.environ['MODEL_NAME'], 'shell-value')
            self.assertEqual(os.environ['MODEL_API_KEY'], 'literal-$TOKEN')

    def test_invalid_key_rejects_entire_file(self):
        file = temporary_workspace(self)/'local.env'
        file.write_text('MODEL_NAME=test\nPATH=unexpected\n', encoding='utf-8')
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                load_env(file)
            self.assertNotIn('MODEL_NAME', os.environ)
