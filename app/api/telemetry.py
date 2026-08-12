"""OTLP/JSON trajectory ingest API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException

from app.telemetry.service import telemetry_service

router = APIRouter(tags=["telemetry"])


@router.post("/v1/traces")
async def export_traces(
    payload: dict[str, Any],
    x_operator: str | None = Header(None, alias="X-Operator"),
    promote: bool = True,
):
    """Accept OTLP/JSON-compatible trace export; optionally promote anomalies to incidents."""
    operator = (x_operator or "otel").strip() or "otel"
    result = await telemetry_service.ingest_otlp_json(payload, promote=promote, operator=operator)
    return result.model_dump()


@router.get("/telemetry/runs")
async def list_runs(limit: int = 20):
    return {"runs": telemetry_service.list_runs(limit=min(limit, 100))}


@router.get("/telemetry/runs/{run_id}")
async def get_run(run_id: str):
    run = telemetry_service.get_run(run_id)
    if not run:
        raise HTTPException(404, f"Unknown run: {run_id}")
    return run
