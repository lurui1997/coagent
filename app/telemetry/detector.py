"""Detect incident-worthy signals from observed trajectories."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from app.models.event import AgentEvent
from app.telemetry.models import TelemetrySpan
from app.timeutil import now_iso


@dataclass
class Detection:
    symptom: str
    event_type: str
    agent_id: str
    agent_name: str
    error: str | None
    log_snippet: str
    cost_yuan_today: float = 0.0
    budget_yuan_daily: float = 0.0
    retry_webhook: str | None = None


def _attr(spans: list[TelemetrySpan], key: str) -> Any:
    for sp in reversed(spans):
        if key in sp.attributes:
            return sp.attributes[key]
        if key in sp.resource_attributes:
            return sp.resource_attributes[key]
    return None


def detect_anomaly(spans: list[TelemetrySpan]) -> Detection | None:
    """Return a Detection when trajectory indicates an Agent Ops incident."""
    if not spans:
        return None

    agent_id = str(_attr(spans, "coagent.agent_id") or _attr(spans, "service.name") or "unknown-agent")
    agent_name = str(_attr(spans, "coagent.agent_name") or agent_id)

    explicit = _attr(spans, "coagent.symptom")
    event_type = _attr(spans, "coagent.event_type")
    if explicit:
        return Detection(
            symptom=str(explicit),
            event_type=str(event_type or ("cost_report" if explicit == "over_budget" else "run_fail")),
            agent_id=agent_id,
            agent_name=agent_name,
            error=_first_error_message(spans),
            log_snippet=_log_snippet(spans),
            cost_yuan_today=float(_attr(spans, "coagent.cost_yuan_today") or 0.0),
            budget_yuan_daily=float(_attr(spans, "coagent.budget_yuan_daily") or 0.0),
            retry_webhook=_opt_str(_attr(spans, "coagent.retry_webhook")),
        )

    for sp in spans:
        attrs = sp.attributes
        msg = (sp.status_message or "") + " " + str(attrs.get("error.type", ""))
        combined = msg.lower()
        if sp.status_code == "ERROR" or attrs.get("error") is True:
            if ("rate" in combined and "limit" in combined) or "429" in combined:
                return Detection(
                    symptom="rate_limit",
                    event_type="run_fail",
                    agent_id=agent_id,
                    agent_name=agent_name,
                    error=(sp.status_message or "触发 API 限流（rate_limit）")[:2000],
                    log_snippet=_log_snippet(spans),
                    retry_webhook=_opt_str(_attr(spans, "coagent.retry_webhook")),
                )
            if ("empty" in combined and "retrieval" in combined) or attrs.get("gen_ai.retrieval.empty"):
                return Detection(
                    symptom="empty_retrieval",
                    event_type="run_fail",
                    agent_id=agent_id,
                    agent_name=agent_name,
                    error=(sp.status_message or "检索为空（empty_retrieval）")[:2000],
                    log_snippet=_log_snippet(spans),
                )
            if "budget" in combined or "over_budget" in combined:
                return Detection(
                    symptom="over_budget",
                    event_type="cost_report",
                    agent_id=agent_id,
                    agent_name=agent_name,
                    error=(sp.status_message or "日成本超预算（over_budget）")[:2000],
                    log_snippet=_log_snippet(spans),
                    cost_yuan_today=float(_attr(spans, "coagent.cost_yuan_today") or 0.0),
                    budget_yuan_daily=float(_attr(spans, "coagent.budget_yuan_daily") or 0.0),
                )

    return None


def detection_to_event(detection: Detection) -> AgentEvent:
    return AgentEvent(
        event_id=f"evt-otel-{detection.agent_id}-{uuid4().hex[:12]}",
        agent_id=detection.agent_id,
        agent_name=detection.agent_name,
        type=detection.event_type,
        symptom=detection.symptom,
        error=detection.error,
        log_snippet=detection.log_snippet[:2000],
        cost_yuan_today=detection.cost_yuan_today,
        budget_yuan_daily=detection.budget_yuan_daily,
        retry_webhook=detection.retry_webhook,
        ts=now_iso(),
    )


def _first_error_message(spans: list[TelemetrySpan]) -> str | None:
    for sp in spans:
        if sp.status_code == "ERROR" and sp.status_message:
            return sp.status_message[:2000]
        if sp.attributes.get("error.message"):
            return str(sp.attributes["error.message"])[:2000]
    return None


def _log_snippet(spans: list[TelemetrySpan]) -> str:
    parts: list[str] = []
    for sp in spans:
        bit = f"{sp.name}:{sp.status_code}"
        if sp.status_message:
            bit += f"/{sp.status_message[:80]}"
        parts.append(bit)
    return "; ".join(parts)[:2000]


def _opt_str(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return str(value)
