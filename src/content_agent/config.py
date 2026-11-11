"""Explicit local env-file loader; no evaluation or shell interpolation."""
import os
from pathlib import Path

ALLOWED = {'MODEL_URL', 'MODEL_NAME', 'MODEL_API_KEY', 'MODEL_TIMEOUT',
           'MODEL_MAX_TOKENS', 'MODEL_THINKING', 'MODEL_JSON_OUTPUT'}


def load_env(path):
    values = {}
    for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        key, separator, value = line.partition('=')
        key, value = key.strip(), value.strip()
        if not separator or key not in ALLOWED:
            raise ValueError('unsupported env-file entry')
        if value.startswith(('"', "'")):
            if len(value) < 2 or value[-1] != value[0]:
                raise ValueError('unmatched env-file quote')
            value = value[1:-1]
        values[key] = value
    for key, value in values.items():
        os.environ.setdefault(key, value)
