from fastapi import APIRouter, HTTPException

from app.models.event import AgentEvent
from app.orchestrator import orchestrator

router = APIRouter(tags=["events"])


@router.post("/events")
async def receive_event(event: AgentEvent):
    try:
        return await orchestrator.process_event(event)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
