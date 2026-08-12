"""OTLP/JSON-compatible trajectory models (GenAI semantic convention subset)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TelemetrySpan(BaseModel):
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    name: str
    kind: str = "INTERNAL"
    start_time_unix_nano: int | None = None
    end_time_unix_nano: int | None = None
    status_code: str = "UNSET"  # UNSET | OK | ERROR
    status_message: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    resource_attributes: dict[str, Any] = Field(default_factory=dict)


class IngestResult(BaseModel):
    accepted_spans: int
    run_id: str
    agent_id: str | None = None
    detected: bool = False
    incident: dict[str, Any] | None = None
