"""Parse a pragmatic OTLP/JSON traces subset into TelemetrySpan list."""

from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from app.telemetry.models import TelemetrySpan


def _attr_map(attributes: list[dict] | dict | None) -> dict[str, Any]:
    if not attributes:
        return {}
    if isinstance(attributes, dict):
        return dict(attributes)
    out: dict[str, Any] = {}
    for item in attributes:
        key = item.get("key")
        if not key:
            continue
        value = item.get("value") or {}
        if "stringValue" in value:
            out[key] = value["stringValue"]
        elif "intValue" in value:
            out[key] = int(value["intValue"])
        elif "doubleValue" in value:
            out[key] = float(value["doubleValue"])
        elif "boolValue" in value:
            out[key] = bool(value["boolValue"])
        else:
            out[key] = value
    return out


def _status(status: dict | None) -> tuple[str, str | None]:
    if not status:
        return "UNSET", None
    code = status.get("code", "UNSET")
    # OTLP JSON may use numeric enums: 0 UNSET, 1 OK, 2 ERROR
    if code in (0, "STATUS_CODE_UNSET", "UNSET"):
        code_s = "UNSET"
    elif code in (1, "STATUS_CODE_OK", "OK"):
        code_s = "OK"
    elif code in (2, "STATUS_CODE_ERROR", "ERROR"):
        code_s = "ERROR"
    else:
        code_s = str(code)
    return code_s, status.get("message")


def parse_otlp_json(payload: dict[str, Any]) -> list[TelemetrySpan]:
    """Accept OTLP/JSON ExportTraceServiceRequest-like payloads or a flat spans list."""
    if "spans" in payload and isinstance(payload["spans"], list):
        return [_from_flat(s, payload.get("resource", {})) for s in payload["spans"]]

    spans: list[TelemetrySpan] = []
    for rs in payload.get("resourceSpans") or []:
        resource_attrs = _attr_map((rs.get("resource") or {}).get("attributes"))
        for ss in rs.get("scopeSpans") or rs.get("instrumentationLibrarySpans") or []:
            for raw in ss.get("spans") or []:
                spans.append(_from_otlp_span(raw, resource_attrs))
    return spans


def _from_flat(raw: dict[str, Any], resource: dict[str, Any]) -> TelemetrySpan:
    resource_attrs = resource if isinstance(resource, dict) else {}
    if "attributes" in resource_attrs and isinstance(resource_attrs.get("attributes"), list):
        resource_attrs = _attr_map(resource_attrs.get("attributes"))
    status_code, status_message = _status(raw.get("status"))
    return TelemetrySpan(
        trace_id=str(raw.get("traceId") or raw.get("trace_id") or uuid4().hex),
        span_id=str(raw.get("spanId") or raw.get("span_id") or uuid4().hex[:16]),
        parent_span_id=_opt_str(raw.get("parentSpanId") or raw.get("parent_span_id")),
        name=str(raw.get("name") or "span"),
        kind=str(raw.get("kind") or "INTERNAL"),
        start_time_unix_nano=_opt_int(raw.get("startTimeUnixNano") or raw.get("start_time_unix_nano")),
        end_time_unix_nano=_opt_int(raw.get("endTimeUnixNano") or raw.get("end_time_unix_nano")),
        status_code=status_code if raw.get("status") else str(raw.get("status_code") or "UNSET"),
        status_message=status_message or raw.get("status_message"),
        attributes=dict(raw.get("attributes") or {}),
        resource_attributes=resource_attrs,
    )


def _from_otlp_span(raw: dict[str, Any], resource_attrs: dict[str, Any]) -> TelemetrySpan:
    status_code, status_message = _status(raw.get("status"))
    return TelemetrySpan(
        trace_id=str(raw.get("traceId") or uuid4().hex),
        span_id=str(raw.get("spanId") or uuid4().hex[:16]),
        parent_span_id=_opt_str(raw.get("parentSpanId")),
        name=str(raw.get("name") or "span"),
        kind=str(raw.get("kind") or "INTERNAL"),
        start_time_unix_nano=_opt_int(raw.get("startTimeUnixNano")),
        end_time_unix_nano=_opt_int(raw.get("endTimeUnixNano")),
        status_code=status_code,
        status_message=status_message,
        attributes=_attr_map(raw.get("attributes")),
        resource_attributes=resource_attrs,
    )


def _opt_str(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


def _opt_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def build_otlp_json(
    spans: list[TelemetrySpan],
    *,
    service_name: str = "coagent-demo-agent",
) -> dict[str, Any]:
    """Build an OTLP/JSON ExportTraceServiceRequest for demo agents."""
    now = time.time_ns()
    otlp_spans = []
    for sp in spans:
        attrs = [{"key": k, "value": _otlp_value(v)} for k, v in sp.attributes.items()]
        status: dict[str, Any] = {"code": sp.status_code}
        if sp.status_message:
            status["message"] = sp.status_message
        otlp_spans.append(
            {
                "traceId": sp.trace_id,
                "spanId": sp.span_id,
                "parentSpanId": sp.parent_span_id or "",
                "name": sp.name,
                "kind": 1 if sp.kind == "INTERNAL" else 3,
                "startTimeUnixNano": str(sp.start_time_unix_nano or now),
                "endTimeUnixNano": str(sp.end_time_unix_nano or now),
                "attributes": attrs,
                "status": status,
            }
        )

    resource_attrs = [{"key": "service.name", "value": {"stringValue": service_name}}]
    # Merge resource attrs from first span if present
    if spans:
        for k, v in spans[0].resource_attributes.items():
            resource_attrs.append({"key": k, "value": _otlp_value(v)})

    return {
        "resourceSpans": [
            {
                "resource": {"attributes": resource_attrs},
                "scopeSpans": [
                    {
                        "scope": {"name": "coagent.agents", "version": "r1"},
                        "spans": otlp_spans,
                    }
                ],
            }
        ]
    }


def _otlp_value(value: Any) -> dict[str, Any]:
    if isinstance(value, bool):
        return {"boolValue": value}
    if isinstance(value, int):
        return {"intValue": value}
    if isinstance(value, float):
        return {"doubleValue": value}
    return {"stringValue": str(value)}
