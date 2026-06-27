from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import asyncio
import json

from app.db import get_feedback_stats, get_incident, insert_feedback, list_incidents
from app.models.event import AgentEvent
from app.orchestrator import orchestrator
from app.sse import sse_manager

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/trigger/{scenario_id}")
async def trigger_scenario(scenario_id: str):
    if scenario_id not in ("s1", "s2", "s3"):
        raise HTTPException(404, "Unknown scenario")
    event = orchestrator.load_scenario(scenario_id)
    result = await orchestrator.process_event(event, scenario_id=scenario_id)
    return result


@router.get("/incidents")
async def get_incidents():
    return list_incidents()


@router.get("/incidents/{trace_id}")
async def get_incident_detail(trace_id: str):
    incident = get_incident(trace_id)
    if not incident:
        raise HTTPException(404, "Not found")
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
async def submit_feedback(trace_id: str, rating: str, comment: str | None = None):
    incident = get_incident(trace_id)
    if not incident:
        raise HTTPException(404, "Not found")
    if rating not in ("up", "down"):
        raise HTTPException(400, "rating must be up or down")
    insert_feedback(incident["id"], rating, comment)
    return {"status": "ok"}


@router.get("/stats")
async def get_stats():
    return get_feedback_stats()


@router.post("/replay/{trace_id}")
async def replay_incident(trace_id: str):
    try:
        return await orchestrator.replay(trace_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
