"""Workspace-local fixtures (avoid restrictive Windows tempfile ACLs)."""
from pathlib import Path
import shutil
import uuid


def temporary_workspace(test):
    root = Path('.tmp').resolve()
    path = root / ('test-' + uuid.uuid4().hex)
    path.mkdir(parents=True)

    def cleanup():
        if path.resolve().parent != root:
            raise ValueError('test cleanup escaped workspace')
        shutil.rmtree(path)

    test.addCleanup(cleanup)
    return path
