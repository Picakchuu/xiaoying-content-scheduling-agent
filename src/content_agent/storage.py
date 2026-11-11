"""SQLite transaction boundary for request identity, snapshots and saved plans."""
from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3


class ConflictError(ValueError):
    pass


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, state TEXT NOT NULL)")
            conn.execute("CREATE TABLE IF NOT EXISTS plans (request_id TEXT PRIMARY KEY, plan_id TEXT UNIQUE NOT NULL, payload TEXT NOT NULL)")

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path, timeout=10)
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    def start(self, request):
        with self.connect() as conn:
            row = conn.execute("SELECT fingerprint, state FROM runs WHERE id=?", (request.request_id,)).fetchone()
            if row:
                if row[0] != request.fingerprint():
                    raise ConflictError("request_id already belongs to different input")
                return json.loads(row[1]), True
            state = dict(request_id=request.request_id, theme=request.theme, budget=request.budget,
                         deadline=request.deadline.isoformat(), status="running", revision=0,
                         actual_tool_cost=0, elapsed_minutes=0, plan_version=0,
                         materials=[], script=None, estimate=None, steps=[], observations=[],
                         saved_plan_id=None, reason=None, fault_used=[])
            conn.execute("INSERT INTO runs VALUES (?, ?, ?)",
                         (request.request_id, request.fingerprint(), json.dumps(state, ensure_ascii=False)))
            return state, False

    def read(self, request_id):
        with self.connect() as conn:
            return self.load(conn, request_id)

    @staticmethod
    def load(conn, request_id):
        row = conn.execute("SELECT state FROM runs WHERE id=?", (request_id,)).fetchone()
        if row is None:
            raise KeyError(request_id)
        return json.loads(row[0])

    @staticmethod
    def write(conn, state):
        state["revision"] += 1
        conn.execute("UPDATE runs SET state=? WHERE id=?",
                     (json.dumps(state, ensure_ascii=False), state["request_id"]))
