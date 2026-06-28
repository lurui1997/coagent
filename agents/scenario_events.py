from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings
from app.models.event import AgentEvent


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def new_event_id(agent_id: str) -> str:
    return f"evt-{agent_id}-{uuid.uuid4().hex[:12]}"


def load_scenario_event(scenario_id: str, *, agent_id: str | None = None) -> AgentEvent:
    path = settings.data_dir / "scenarios" / f"{scenario_id}.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    data["event_id"] = new_event_id(data["agent_id"])
    data["ts"] = _now_iso()
    if agent_id:
        data["agent_id"] = agent_id
    coagent_base = settings.coagent_public_url.rstrip("/")
    if scenario_id == "s1" and data.get("retry_webhook"):
        data["retry_webhook"] = f"{coagent_base}/agents/retry/cs-bot"
    return AgentEvent.model_validate(data)


def build_rate_limit_event(
    agent_id: str,
    agent_name: str,
    error: str,
    log_snippet: str,
    *,
    coagent_base: str,
) -> AgentEvent:
    return AgentEvent(
        event_id=new_event_id(agent_id),
        agent_id=agent_id,
        agent_name=agent_name,
        type="run_fail",
        symptom="rate_limit",
        error=error[:2000],
        log_snippet=log_snippet[:2000],
        cost_yuan_today=8.5,
        budget_yuan_daily=20.0,
        retry_webhook=f"{coagent_base.rstrip('/')}/agents/retry/cs-bot",
        ts=_now_iso(),
    )


def build_empty_retrieval_event(
    agent_id: str,
    agent_name: str,
    query: str,
    log_snippet: str,
) -> AgentEvent:
    return AgentEvent(
        event_id=new_event_id(agent_id),
        agent_id=agent_id,
        agent_name=agent_name,
        type="run_fail",
        symptom="empty_retrieval",
        error="Retrieval returned 0 chunks above threshold 0.7",
        log_snippet=log_snippet[:2000] or f"query={query!r}; empty_retrieval_rate=35%",
        cost_yuan_today=12.0,
        budget_yuan_daily=30.0,
        retry_webhook=None,
        ts=_now_iso(),
    )


def build_over_budget_event(
    agent_id: str,
    agent_name: str,
    cost_yuan: float,
    budget_yuan: float,
    log_snippet: str,
) -> AgentEvent:
    return AgentEvent(
        event_id=new_event_id(agent_id),
        agent_id=agent_id,
        agent_name=agent_name,
        type="cost_report",
        symptom="over_budget",
        error=None,
        log_snippet=log_snippet[:2000],
        cost_yuan_today=cost_yuan,
        budget_yuan_daily=budget_yuan,
        retry_webhook=None,
        ts=_now_iso(),
    )
