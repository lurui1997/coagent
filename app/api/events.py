from fastapi import APIRouter, Header, HTTPException

from app.models.event import AgentEvent
from app.orchestrator import orchestrator

router = APIRouter(tags=["events"])


@router.post("/events")
async def receive_event(event: AgentEvent, x_operator: str | None = Header(None, alias="X-Operator")):
    operator = (x_operator or "webhook").strip() or "webhook"
    try:
        return await orchestrator.process_event(event, operator=operator)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
