"""Trajectory ingest service: store spans, detect anomalies, promote to incidents."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.telemetry.detector import detect_anomaly, detection_to_event
from app.telemetry.models import IngestResult, TelemetrySpan
from app.telemetry.otlp_json import parse_otlp_json
from app.telemetry.store import (
    get_trajectory_run,
    init_trajectory_tables,
    list_trajectory_runs,
    save_trajectory_run,
    update_run_incident,
)


class TelemetryService:
    def ensure_schema(self) -> None:
        init_trajectory_tables()

    async def ingest_otlp_json(
        self,
        payload: dict[str, Any],
        *,
        promote: bool = True,
        operator: str = "otel",
    ) -> IngestResult:
        from app.orchestrator import orchestrator

        spans = parse_otlp_json(payload)
        if not spans:
            return IngestResult(accepted_spans=0, run_id="run-empty")

        run_id = str(
            _first_attr(spans, "coagent.run_id")
            or spans[0].trace_id
            or f"run-{uuid4().hex[:12]}"
        )
        agent_id = _opt_str(_first_attr(spans, "coagent.agent_id"))
        service_name = _opt_str(_first_attr(spans, "service.name"))
        detection = detect_anomaly(spans)
        has_error = bool(detection) or any(s.status_code == "ERROR" for s in spans)

        save_trajectory_run(
            run_id,
            spans,
            agent_id=agent_id,
            service_name=service_name,
            has_error=has_error,
            detected_symptom=detection.symptom if detection else None,
        )

        incident: dict[str, Any] | None = None
        if promote and detection:
            event = detection_to_event(detection)
            incident = await orchestrator.process_event(event, operator=operator)
            update_run_incident(
                run_id,
                detected_symptom=detection.symptom,
                incident_trace_id=str(incident.get("trace_id")),
            )

        return IngestResult(
            accepted_spans=len(spans),
            run_id=run_id,
            agent_id=agent_id,
            detected=bool(detection),
            incident=incident,
        )

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        return get_trajectory_run(run_id)

    def list_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        return list_trajectory_runs(limit)


def _first_attr(spans: list[TelemetrySpan], key: str) -> Any:
    for sp in spans:
        if key in sp.attributes:
            return sp.attributes[key]
        if key in sp.resource_attributes:
            return sp.resource_attributes[key]
    return None


def _opt_str(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


telemetry_service = TelemetryService()
