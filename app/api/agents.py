"""CoAgent 本地 Claude Agent HTTP API。"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from agents.registry import AGENT_IDS, get_agent
from app.db import insert_audit_action

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agents", tags=["agents"])


class RunAgentRequest(BaseModel):
    mode: str = Field(default="simulate", pattern="^(live|simulate)$")
    query: str | None = None
    task: str | None = None
    template: str = Field(default="longform", pattern="^(standard|longform|batch)$")


def _operator(x_operator: str | None) -> str:
    return (x_operator or "agents-api").strip() or "agents-api"


@router.get("")
async def list_agents():
    return {"agents": list(AGENT_IDS)}


@router.post("/{agent_id}/run")
async def run_agent(
    agent_id: str,
    body: RunAgentRequest,
    x_operator: str | None = Header(None, alias="X-Operator"),
):
    if agent_id not in AGENT_IDS:
        raise HTTPException(404, f"Unknown agent: {agent_id}")
    operator = _operator(x_operator)
    agent = get_agent(agent_id)
    try:
        if body.mode == "simulate":
            result = agent.run_simulate()
        elif agent_id == "content-bot":
            result = agent.run_live(body.task or "营销长文案", template=body.template)
        elif agent_id == "rag-bot":
            if not body.query:
                raise HTTPException(400, "rag-bot live 需要 query")
            result = agent.run_live(body.query)
        else:
            if not body.query:
                raise HTTPException(400, "cs-bot live 需要 query")
            result = agent.run_live(body.query)
    except Exception as e:
        logger.exception("Agent run failed: %s", agent_id)
        raise HTTPException(502, str(e)) from e

    trace_id = (result.get("coagent") or {}).get("trace_id")
    if trace_id:
        insert_audit_action(trace_id, "agent_run", operator, {"agent_id": agent_id, **result})
    return result


@router.get("/content-bot/cost")
async def content_bot_cost():
    agent = get_agent("content-bot")
    return agent.get_cost_status()


@router.post("/content-bot/cost/reset")
async def content_bot_cost_reset(x_operator: str | None = Header(None, alias="X-Operator")):
    agent = get_agent("content-bot")
    result = agent.reset_cost()
    insert_audit_action("content-bot", "cost_reset", _operator(x_operator), result)
    return result


@router.post("/retry/{agent_id}")
async def retry_agent(agent_id: str, x_operator: str | None = Header(None, alias="X-Operator")):
    if agent_id != "cs-bot":
        raise HTTPException(404, "Only cs-bot supports retry")
    operator = _operator(x_operator)
    agent = get_agent("cs-bot")
    result = agent.retry()
    insert_audit_action(
        f"retry-{agent_id}",
        "agent_retry",
        operator,
        {"agent_id": agent_id, **result},
    )
    return result
