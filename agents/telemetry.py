"""Build GenAI-flavored trajectory spans for demo agents (R1)."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from app.models.event import AgentEvent
from app.telemetry.models import TelemetrySpan
from app.telemetry.otlp_json import build_otlp_json


@dataclass
class SimulateBundle:
    event: AgentEvent
    spans: list[TelemetrySpan]
    agent_id: str
    mode: str = "simulate"

    def to_otlp(self) -> dict[str, Any]:
        return build_otlp_json(self.spans, service_name=self.agent_id)

    def as_result(self, coagent: dict[str, Any], telemetry: dict[str, Any] | None = None) -> dict[str, Any]:
        out = {
            "agent": self.agent_id,
            "mode": self.mode,
            "coagent": coagent,
        }
        if telemetry is not None:
            out["telemetry"] = telemetry
        return out


def _ids() -> tuple[str, str, str]:
    trace_id = uuid4().hex
    root_id = uuid4().hex[:16]
    child_id = uuid4().hex[:16]
    return trace_id, root_id, child_id


def spans_from_event(event: AgentEvent, *, run_id: str | None = None) -> list[TelemetrySpan]:
    """Create a minimal trajectory that encodes the demo incident for Inline Observer."""
    now = time.time_ns()
    trace_id, root_id, child_id = _ids()
    run_id = run_id or f"run-{event.agent_id}-{uuid4().hex[:10]}"
    resource = {
        "service.name": event.agent_id,
        "coagent.agent_id": event.agent_id,
        "coagent.agent_name": event.agent_name,
    }
    root = TelemetrySpan(
        trace_id=trace_id,
        span_id=root_id,
        name=f"agent.run/{event.agent_id}",
        kind="INTERNAL",
        start_time_unix_nano=now - 2_000_000,
        end_time_unix_nano=now,
        status_code="ERROR",
        status_message=event.error or event.symptom,
        attributes={
            "coagent.run_id": run_id,
            "coagent.agent_id": event.agent_id,
            "coagent.agent_name": event.agent_name,
            "coagent.event_type": event.type,
            "coagent.symptom": event.symptom,
            "coagent.cost_yuan_today": event.cost_yuan_today,
            "coagent.budget_yuan_daily": event.budget_yuan_daily,
            **({"coagent.retry_webhook": event.retry_webhook} if event.retry_webhook else {}),
        },
        resource_attributes=resource,
    )
    child_name = "gen_ai.chat"
    child_attrs: dict[str, Any] = {
        "gen_ai.operation.name": "chat",
        "coagent.agent_id": event.agent_id,
        "coagent.symptom": event.symptom,
        "coagent.event_type": event.type,
        "coagent.run_id": run_id,
    }
    if event.symptom == "empty_retrieval":
        child_name = "gen_ai.retrieval"
        child_attrs["gen_ai.retrieval.empty"] = True
    elif event.symptom == "over_budget":
        child_name = "gen_ai.client.tokens"
        child_attrs["coagent.cost_yuan_today"] = event.cost_yuan_today
        child_attrs["coagent.budget_yuan_daily"] = event.budget_yuan_daily
    elif event.symptom == "rate_limit":
        child_attrs["error.type"] = "rate_limit"
        child_attrs["http.response.status_code"] = 429

    child = TelemetrySpan(
        trace_id=trace_id,
        span_id=child_id,
        parent_span_id=root_id,
        name=child_name,
        kind="CLIENT",
        start_time_unix_nano=now - 1_500_000,
        end_time_unix_nano=now - 100_000,
        status_code="ERROR",
        status_message=event.error or event.symptom,
        attributes=child_attrs,
        resource_attributes=resource,
    )
    return [root, child]
