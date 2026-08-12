"""SQLite persistence for observed trajectories (R1 Inline Observer)."""

from __future__ import annotations

import json
from typing import Any

from app.db import get_db
from app.telemetry.models import TelemetrySpan
from app.timeutil import now_iso

TRAJECTORY_SCHEMA = """
CREATE TABLE IF NOT EXISTS trajectory_runs (
  run_id TEXT PRIMARY KEY,
  agent_id TEXT,
  service_name TEXT,
  span_count INTEGER NOT NULL,
  has_error INTEGER NOT NULL DEFAULT 0,
  detected_symptom TEXT,
  incident_trace_id TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS trajectory_spans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL REFERENCES trajectory_runs(run_id),
  trace_id TEXT NOT NULL,
  span_id TEXT NOT NULL,
  parent_span_id TEXT,
  name TEXT NOT NULL,
  status_code TEXT NOT NULL,
  status_message TEXT,
  attributes_json TEXT NOT NULL,
  resource_json TEXT NOT NULL,
  start_time_unix_nano INTEGER,
  end_time_unix_nano INTEGER
);

CREATE INDEX IF NOT EXISTS idx_trajectory_spans_run ON trajectory_spans(run_id);
CREATE INDEX IF NOT EXISTS idx_trajectory_runs_agent ON trajectory_runs(agent_id);
"""


def init_trajectory_tables() -> None:
    with get_db() as conn:
        conn.executescript(TRAJECTORY_SCHEMA)


def save_trajectory_run(
    run_id: str,
    spans: list[TelemetrySpan],
    *,
    agent_id: str | None,
    service_name: str | None,
    has_error: bool,
    detected_symptom: str | None = None,
    incident_trace_id: str | None = None,
) -> None:
    with get_db() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO trajectory_runs
               (run_id, agent_id, service_name, span_count, has_error, detected_symptom, incident_trace_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id,
                agent_id,
                service_name,
                len(spans),
                1 if has_error else 0,
                detected_symptom,
                incident_trace_id,
                now_iso(),
            ),
        )
        conn.execute("DELETE FROM trajectory_spans WHERE run_id = ?", (run_id,))
        for sp in spans:
            conn.execute(
                """INSERT INTO trajectory_spans
                   (run_id, trace_id, span_id, parent_span_id, name, status_code, status_message,
                    attributes_json, resource_json, start_time_unix_nano, end_time_unix_nano)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    run_id,
                    sp.trace_id,
                    sp.span_id,
                    sp.parent_span_id,
                    sp.name,
                    sp.status_code,
                    sp.status_message,
                    json.dumps(sp.attributes, ensure_ascii=False),
                    json.dumps(sp.resource_attributes, ensure_ascii=False),
                    sp.start_time_unix_nano,
                    sp.end_time_unix_nano,
                ),
            )


def update_run_incident(run_id: str, *, detected_symptom: str, incident_trace_id: str) -> None:
    with get_db() as conn:
        conn.execute(
            """UPDATE trajectory_runs
               SET detected_symptom = ?, incident_trace_id = ?, has_error = 1
               WHERE run_id = ?""",
            (detected_symptom, incident_trace_id, run_id),
        )


def get_trajectory_run(run_id: str) -> dict[str, Any] | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM trajectory_runs WHERE run_id = ?", (run_id,)).fetchone()
        if not row:
            return None
        spans = conn.execute(
            "SELECT * FROM trajectory_spans WHERE run_id = ? ORDER BY id",
            (run_id,),
        ).fetchall()
    return {
        "run_id": row["run_id"],
        "agent_id": row["agent_id"],
        "service_name": row["service_name"],
        "span_count": row["span_count"],
        "has_error": bool(row["has_error"]),
        "detected_symptom": row["detected_symptom"],
        "incident_trace_id": row["incident_trace_id"],
        "created_at": row["created_at"],
        "spans": [
            {
                "trace_id": s["trace_id"],
                "span_id": s["span_id"],
                "parent_span_id": s["parent_span_id"],
                "name": s["name"],
                "status_code": s["status_code"],
                "status_message": s["status_message"],
                "attributes": json.loads(s["attributes_json"]),
                "resource_attributes": json.loads(s["resource_json"]),
            }
            for s in spans
        ],
    }


def list_trajectory_runs(limit: int = 20) -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT run_id, agent_id, service_name, span_count, has_error, detected_symptom,
                      incident_trace_id, created_at
               FROM trajectory_runs ORDER BY created_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]
