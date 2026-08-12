from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from app.timeutil import now_iso

DEFAULT_DB = Path("data/showcase_faq_metrics.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS ask_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  query TEXT NOT NULL,
  empty_retrieval INTEGER NOT NULL,
  hallucination_risk INTEGER NOT NULL,
  latency_ms INTEGER NOT NULL,
  prompt_tokens INTEGER DEFAULT 0,
  completion_tokens INTEGER DEFAULT 0,
  est_cost_yuan REAL DEFAULT 0,
  incident_promoted INTEGER NOT NULL DEFAULT 0,
  incident_trace_id TEXT,
  status TEXT NOT NULL
);
"""


class MetricsStore:
    def __init__(self, db_path: Path | str | None = None):
        self.db_path = Path(db_path or DEFAULT_DB)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init(self) -> None:
        with self._conn() as conn:
            conn.executescript(SCHEMA)

    def record(self, row: dict[str, Any]) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO ask_events
                   (ts, query, empty_retrieval, hallucination_risk, latency_ms,
                    prompt_tokens, completion_tokens, est_cost_yuan,
                    incident_promoted, incident_trace_id, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    row.get("ts") or now_iso(),
                    row["query"],
                    1 if row.get("empty_retrieval") else 0,
                    1 if row.get("hallucination_risk") else 0,
                    int(row.get("latency_ms") or 0),
                    int(row.get("prompt_tokens") or 0),
                    int(row.get("completion_tokens") or 0),
                    float(row.get("est_cost_yuan") or 0),
                    1 if row.get("incident_promoted") else 0,
                    row.get("incident_trace_id"),
                    row.get("status") or "ok",
                ),
            )
            return int(cur.lastrowid)

    def summary(self) -> dict[str, Any]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM ask_events ORDER BY id DESC LIMIT 500"
            ).fetchall()
        n = len(rows)
        if n == 0:
            return {
                "ask_count": 0,
                "empty_retrieval_rate": 0.0,
                "hallucination_risk_rate": 0.0,
                "p50_latency_ms": 0,
                "p95_latency_ms": 0,
                "token_usage": 0,
                "est_cost_yuan": 0.0,
                "incident_promotions": 0,
                "recent": [],
            }
        empty = sum(r["empty_retrieval"] for r in rows)
        hallu = sum(r["hallucination_risk"] for r in rows)
        promoted = sum(r["incident_promoted"] for r in rows)
        latencies = sorted(r["latency_ms"] for r in rows)
        tokens = sum((r["prompt_tokens"] or 0) + (r["completion_tokens"] or 0) for r in rows)
        cost = sum(r["est_cost_yuan"] or 0 for r in rows)

        def pct(p: float) -> int:
            if not latencies:
                return 0
            idx = min(len(latencies) - 1, max(0, int(round((p / 100) * (len(latencies) - 1)))))
            return int(latencies[idx])

        return {
            "ask_count": n,
            "empty_retrieval_rate": round(empty / n, 4),
            "hallucination_risk_rate": round(hallu / n, 4),
            "p50_latency_ms": pct(50),
            "p95_latency_ms": pct(95),
            "token_usage": tokens,
            "est_cost_yuan": round(cost, 4),
            "incident_promotions": promoted,
            "recent": [dict(r) for r in rows[:20]],
        }
