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
        "message": "重试已执行，Agent 开始恢复",
        "steps": [
            {"id": "config", "label": "降低 concurrent 10 → 5", "status": "done"},
            {"id": "webhook", "label": "触发 Retry Webhook", "status": "done"},
            {"id": "verify", "label": "验证失败率回落", "status": "done"},
        ],
    }
