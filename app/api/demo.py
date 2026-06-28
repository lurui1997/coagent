from fastapi import APIRouter, Header

from app.db import insert_audit_action

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/retry/{agent_id}")
async def demo_retry(agent_id: str, x_operator: str | None = Header(None, alias="X-Operator")):
    operator = (x_operator or "demo").strip() or "demo"
    insert_audit_action(
        f"retry-{agent_id}",
        "demo_retry",
        operator,
        {"agent_id": agent_id},
    )
    return {
        "status": "ok",
        "agent_id": agent_id,
        "operator": operator,
        "message": "retry scheduled (demo)",
    }
