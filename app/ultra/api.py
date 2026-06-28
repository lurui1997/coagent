import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import get_incident, list_audit_actions, list_incidents
from app.playbooks.engine import PlaybookEngine
from app.ultra.historical import find_similar_incidents, simulate_what_if
from app.ultra.knowledge_graph import build_knowledge_graph, query_multi_hop
from app.ultra.team_orchestrator import build_team_plan, select_orchestration_mode

router = APIRouter(prefix="/admin/ultra", tags=["ultra"])

_engine = PlaybookEngine()
SCENARIO_PLAYBOOK = {"s1": "cs_rate_limit", "s2": "rag_empty_retrieval", "s3": "cost_over_budget"}


class WhatIfRequest(BaseModel):
    changes: dict = {}


@router.get("/graph")
async def get_knowledge_graph(limit: int = 50):
    incidents = list_incidents(limit)
    playbooks = {pb["id"]: pb for pb in _load_playbooks()}
    graph = build_knowledge_graph(incidents, playbooks)
    return graph


@router.get("/graph/agent/{agent_id}")
async def get_agent_graph(agent_id: str, limit: int = 50):
    incidents = [i for i in list_incidents(limit) if i["agent_id"] == agent_id]
    playbooks = {pb["id"]: pb for pb in _load_playbooks()}
    graph = build_knowledge_graph(incidents, playbooks)
    paths = query_multi_hop(graph, agent_id)
    return {"graph": graph, "multi_hop": paths}


@router.get("/incidents/{trace_id}/similar")
async def get_similar_incidents(trace_id: str, limit: int = 5):
    target = get_incident(trace_id)
    if not target:
        raise HTTPException(404, "Not found")
    all_incidents = list_incidents(100)
    similar = find_similar_incidents(target, all_incidents, limit=limit)
    return {"trace_id": trace_id, "similar": similar, "count": len(similar)}


@router.post("/incidents/{trace_id}/what-if")
async def run_what_if(trace_id: str, body: WhatIfRequest):
    incident = get_incident(trace_id)
    if not incident:
        raise HTTPException(404, "Not found")
    playbook_id = SCENARIO_PLAYBOOK.get(incident.get("scenario_id", ""), incident.get("scenario_id", ""))
    try:
        playbook = _engine.get(playbook_id)
    except KeyError as e:
        raise HTTPException(400, f"Unknown playbook: {playbook_id}") from e
    return simulate_what_if(incident, playbook, body.changes)


@router.get("/incidents/{trace_id}/team-plan")
async def get_team_plan(trace_id: str):
    incident = get_incident(trace_id)
    if not incident:
        raise HTTPException(404, "Not found")
    from app.models.event import AgentEvent

    event = AgentEvent.model_validate(incident["event_json"])
    playbook_id = SCENARIO_PLAYBOOK.get(incident.get("scenario_id", ""), "")
    score_total = (incident.get("score_json") or {}).get("total")
    mode = select_orchestration_mode(event, playbook_id, score_total)
    plan = build_team_plan(mode, event, playbook_id)
    return {"trace_id": trace_id, **plan}


def _load_playbooks() -> list[dict]:
    path = Path("data/ops_playbooks.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)["playbooks"]
