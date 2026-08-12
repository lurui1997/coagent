from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from app.telemetry.models import TelemetrySpan
from app.telemetry.otlp_json import build_otlp_json


def build_empty_retrieval_otlp(
    *,
    query: str,
    agent_id: str = "showcase-faq-agent",
    agent_name: str = "Showcase FAQ Agent",
) -> dict[str, Any]:
    now = time.time_ns()
    trace_id = uuid4().hex
    root_id = uuid4().hex[:16]
    child_id = uuid4().hex[:16]
    run_id = f"run-faq-{uuid4().hex[:10]}"
    resource = {
        "service.name": agent_id,
        "coagent.agent_id": agent_id,
        "coagent.agent_name": agent_name,
    }
    root = TelemetrySpan(
        trace_id=trace_id,
        span_id=root_id,
        name=f"agent.run/{agent_id}",
        kind="INTERNAL",
        start_time_unix_nano=now - 2_000_000,
        end_time_unix_nano=now,
        status_code="ERROR",
        status_message="empty_retrieval：检索返回 0 个片段",
        attributes={
            "coagent.run_id": run_id,
            "coagent.agent_id": agent_id,
            "coagent.agent_name": agent_name,
            "coagent.event_type": "run_fail",
            "coagent.symptom": "empty_retrieval",
            "coagent.query": query[:200],
        },
        resource_attributes=resource,
    )
    child = TelemetrySpan(
        trace_id=trace_id,
        span_id=child_id,
        parent_span_id=root_id,
        name="gen_ai.retrieval",
        kind="CLIENT",
        start_time_unix_nano=now - 1_500_000,
        end_time_unix_nano=now - 100_000,
        status_code="ERROR",
        status_message="检索未返回高于阈值的片段（0 chunks / empty_retrieval）",
        attributes={
            "gen_ai.retrieval.empty": True,
            "coagent.agent_id": agent_id,
            "coagent.symptom": "empty_retrieval",
            "coagent.event_type": "run_fail",
            "coagent.run_id": run_id,
            "coagent.query": query[:200],
        },
        resource_attributes=resource,
    )
    return build_otlp_json([root, child], service_name=agent_id)
