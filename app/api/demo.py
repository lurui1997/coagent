from fastapi import APIRouter

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/retry/{agent_id}")
async def demo_retry(agent_id: str):
    return {
        "status": "ok",
        "agent_id": agent_id,
        "message": "retry scheduled (demo)",
    }
