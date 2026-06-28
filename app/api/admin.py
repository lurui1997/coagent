import asyncio
import csv
import io
import json
import logging

import httpx
from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse

from app.config import settings
from app.correction.suggestions import build_correction_suggestions
from app.db import (
    export_audit_records,
    get_feedback_stats,
    get_incident,
    insert_audit_action,
    insert_feedback,
    list_incidents,
)
from app.orchestrator import orchestrator
from app.sse import sse_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


def _operator(x_operator: str | None) -> str:
    return (x_operator or "system").strip() or "system"


@router.post("/trigger/{scenario_id}")
async def trigger_scenario(scenario_id: str, x_operator: str | None = Header(None, alias="X-Operator")):
    if scenario_id not in ("s1", "s2", "s3"):
        raise HTTPException(404, "Unknown scenario")
    event = orchestrator.load_scenario(scenario_id)
    operator = _operator(x_operator)
    result = await orchestrator.process_event(event, scenario_id=scenario_id, operator=operator)
    if result.get("trace_id") and result.get("status") == "ok":
        insert_audit_action(result["trace_id"], "scenario_trigger", operator, {"scenario_id": scenario_id})
    return result


@router.get("/incidents")
async def get_incidents():
    return list_incidents()


@router.get("/incidents/{trace_id}")
async def get_incident_detail(trace_id: str):
    incident = get_incident(trace_id)
    if not incident:
        raise HTTPException(404, "Not found")
    incident["correction_suggestions"] = build_correction_suggestions(incident)
    return incident


@router.get("/incidents/{trace_id}/stream")
async def stream_incident(trace_id: str):
    async def event_generator():
        q = sse_manager.subscribe(trace_id)
        try:
            incident = get_incident(trace_id)
            if incident and incident.get("timeline_json"):
                for item in incident["timeline_json"]:
                    data = {
                        "type": item["type"],
                        "trace_id": trace_id,
                        "ts": item.get("ts", incident.get("started_at", "")),
                        "payload": item.get("payload", {}),
                    }
                    yield f"event: incident\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

                if incident.get("status") in ("completed", "failed"):
                    return

            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=30.0)
                    yield f"event: incident\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
                    if event["type"] in ("incident_completed", "incident_failed", "replay_completed"):
                        break
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            sse_manager.unsubscribe(trace_id, q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/incidents/{trace_id}/feedback")
async def submit_feedback(
    trace_id: str,
    rating: str,
    comment: str | None = None,
    x_operator: str | None = Header(None, alias="X-Operator"),
):
    incident = get_incident(trace_id)
    if not incident:
        raise HTTPException(404, "Not found")
    if rating not in ("up", "down"):
        raise HTTPException(400, "rating must be up or down")
    operator = _operator(x_operator)
    insert_feedback(incident["id"], rating, comment)
    insert_audit_action(trace_id, "feedback", operator, {"rating": rating, "comment": comment})
    return {"status": "ok"}


@router.get("/stats")
async def get_stats():
    return get_feedback_stats()


@router.post("/replay/{trace_id}")
async def replay_incident(trace_id: str, x_operator: str | None = Header(None, alias="X-Operator")):
    try:
        operator = _operator(x_operator)
        insert_audit_action(trace_id, "replay", operator, {})
        return await orchestrator.replay(trace_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.get("/audit/export")
async def export_audit(format: str = "json"):
    records = export_audit_records()
    if format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "trace_id",
                "event_id",
                "agent_id",
                "scenario_id",
                "status",
                "operator",
                "llm_model",
                "started_at",
                "completed_at",
                "duration_ms",
                "score_total",
                "score_grade",
            ],
        )
        writer.writeheader()
        for row in records:
            writer.writerow({k: row.get(k) for k in writer.fieldnames})
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=coagent_audit.csv"},
        )
    return {"records": records, "count": len(records)}


@router.get("/incidents/{trace_id}/corrections")
async def get_corrections(trace_id: str):
    incident = get_incident(trace_id)
    if not incident:
        raise HTTPException(404, "Not found")
    return {"trace_id": trace_id, "suggestions": build_correction_suggestions(incident)}


@router.post("/incidents/{trace_id}/apply-correction")
async def apply_correction(
    trace_id: str,
    x_operator: str | None = Header(None, alias="X-Operator"),
):
    incident = get_incident(trace_id)
    if not incident:
        raise HTTPException(404, "Not found")
    operator = _operator(x_operator)
    suggestions = build_correction_suggestions(incident)
    if not suggestions:
        raise HTTPException(400, "No correction suggestions for this incident")

    payload = {"suggestions": suggestions, "applied": True}
    insert_audit_action(trace_id, "correction_applied", operator, payload)

    webhook_status = "skipped"
    if settings.correction_webhook_url:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    settings.correction_webhook_url,
                    json={
                        "trace_id": trace_id,
                        "agent_id": incident["agent_id"],
                        "operator": operator,
                        "suggestions": suggestions,
                    },
                )
                webhook_status = "ok" if resp.is_success else f"error_{resp.status_code}"
        except Exception as e:
            logger.warning("Correction webhook failed: %s", e)
            webhook_status = f"failed: {e}"

    return {
        "status": "ok",
        "trace_id": trace_id,
        "operator": operator,
        "suggestions_applied": len(suggestions),
        "webhook_status": webhook_status,
    }
