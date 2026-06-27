import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS incidents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  trace_id TEXT NOT NULL UNIQUE,
  event_id TEXT NOT NULL,
  agent_id TEXT NOT NULL,
  scenario_id TEXT NOT NULL,
  status TEXT NOT NULL,
  event_json TEXT NOT NULL,
  llm_json TEXT,
  score_json TEXT,
  timeline_json TEXT,
  started_at TEXT NOT NULL,
  completed_at TEXT,
  feishu_msg_id TEXT,
  duration_ms INTEGER
);

CREATE INDEX IF NOT EXISTS idx_incidents_event_id_started ON incidents(event_id, started_at);

CREATE TABLE IF NOT EXISTS feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  incident_id INTEGER NOT NULL REFERENCES incidents(id),
  rating TEXT NOT NULL,
  comment TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_daily_stats (
  agent_id TEXT NOT NULL,
  date TEXT NOT NULL,
  run_count INTEGER DEFAULT 0,
  fail_count INTEGER DEFAULT 0,
  cost_yuan REAL DEFAULT 0,
  PRIMARY KEY (agent_id, date)
);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.database_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as conn:
        conn.executescript(SCHEMA)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_trace_id() -> str:
    return f"tr-{uuid4().hex[:12]}"


def find_duplicate_event(event_id: str, within_seconds: int = 600) -> str | None:
    cutoff = (datetime.now(timezone.utc) - timedelta(seconds=within_seconds)).isoformat()
    with get_db() as conn:
        row = conn.execute(
            "SELECT trace_id FROM incidents WHERE event_id = ? AND started_at > ? ORDER BY started_at DESC LIMIT 1",
            (event_id, cutoff),
        ).fetchone()
        return row["trace_id"] if row else None


def insert_incident(
    trace_id: str,
    event_id: str,
    agent_id: str,
    scenario_id: str,
    event_json: dict[str, Any],
) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO incidents (trace_id, event_id, agent_id, scenario_id, status, event_json, timeline_json, started_at)
               VALUES (?, ?, ?, ?, 'running', ?, '[]', ?)""",
            (trace_id, event_id, agent_id, scenario_id, json.dumps(event_json, ensure_ascii=False), utc_now_iso()),
        )
        return cur.lastrowid


def update_incident(
    trace_id: str,
    *,
    status: str | None = None,
    llm_json: dict | None = None,
    score_json: dict | None = None,
    timeline_json: list | None = None,
    feishu_msg_id: str | None = None,
    duration_ms: int | None = None,
) -> None:
    fields: list[str] = []
    values: list[Any] = []
    if status is not None:
        fields.append("status = ?")
        values.append(status)
        if status in ("completed", "failed"):
            fields.append("completed_at = ?")
            values.append(utc_now_iso())
    if llm_json is not None:
        fields.append("llm_json = ?")
        values.append(json.dumps(llm_json, ensure_ascii=False))
    if score_json is not None:
        fields.append("score_json = ?")
        values.append(json.dumps(score_json, ensure_ascii=False))
    if timeline_json is not None:
        fields.append("timeline_json = ?")
        values.append(json.dumps(timeline_json, ensure_ascii=False))
    if feishu_msg_id is not None:
        fields.append("feishu_msg_id = ?")
        values.append(feishu_msg_id)
    if duration_ms is not None:
        fields.append("duration_ms = ?")
        values.append(duration_ms)
    if not fields:
        return
    values.append(trace_id)
    with get_db() as conn:
        conn.execute(f"UPDATE incidents SET {', '.join(fields)} WHERE trace_id = ?", values)


def get_incident(trace_id: str) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM incidents WHERE trace_id = ?", (trace_id,)).fetchone()
        if not row:
            return None
        return _row_to_incident(row)


def list_incidents(limit: int = 50) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM incidents ORDER BY started_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [_row_to_incident(r) for r in rows]


def _row_to_incident(row: sqlite3.Row) -> dict:
    d = dict(row)
    for key in ("event_json", "llm_json", "score_json", "timeline_json"):
        if d.get(key):
            d[key] = json.loads(d[key])
        else:
            d[key] = None if key != "timeline_json" else []
    return d


def upsert_agent_stats(agent_id: str, event_type: str, cost_yuan_today: float) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with get_db() as conn:
        conn.execute(
            """INSERT INTO agent_daily_stats (agent_id, date, run_count, fail_count, cost_yuan)
               VALUES (?, ?, 1, ?, ?)
               ON CONFLICT(agent_id, date) DO UPDATE SET
                 run_count = run_count + 1,
                 fail_count = fail_count + excluded.fail_count,
                 cost_yuan = excluded.cost_yuan""",
            (agent_id, today, 1 if event_type == "run_fail" else 0, cost_yuan_today),
        )


def get_latest_scores() -> dict[str, dict]:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT i.agent_id, i.score_json, i.completed_at
               FROM incidents i
               WHERE i.completed_at IS NOT NULL AND i.score_json IS NOT NULL
               ORDER BY i.completed_at DESC"""
        ).fetchall()
    result: dict[str, dict] = {}
    for row in rows:
        aid = row["agent_id"]
        if aid in result:
            continue
        if row["score_json"]:
            result[aid] = json.loads(row["score_json"])
    return result


def insert_feedback(incident_id: int, rating: str, comment: str | None = None) -> None:
    with get_db() as conn:
        conn.execute(
            "INSERT INTO feedback (incident_id, rating, comment, created_at) VALUES (?, ?, ?, ?)",
            (incident_id, rating, comment, utc_now_iso()),
        )


def get_feedback_stats() -> dict:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT rating, COUNT(*) as cnt FROM feedback GROUP BY rating"
        ).fetchall()
    stats = {"thumbs_up": 0, "thumbs_down": 0, "total": 0}
    for row in rows:
        if row["rating"] == "up":
            stats["thumbs_up"] = row["cnt"]
        elif row["rating"] == "down":
            stats["thumbs_down"] = row["cnt"]
        stats["total"] += row["cnt"]
    return stats
