import pytest

from app.models.event import AgentEvent
from app.ultra.historical import find_similar_incidents, simulate_what_if
from app.ultra.knowledge_graph import build_knowledge_graph, query_multi_hop
from app.ultra.team_orchestrator import build_team_plan, select_orchestration_mode


def _sample_incident(scenario="s1", trace="tr-test"):
    events = {
        "s1": {
            "event_id": "e1",
            "agent_id": "cs-bot",
            "agent_name": "客服 Agent",
            "type": "run_fail",
            "symptom": "rate_limit",
            "error": "429 rate limit",
            "log_snippet": "concurrent=10 rate_limit exceeded",
            "ts": "2026-06-28T00:00:00Z",
            "retry_webhook": "http://x",
            "cost_yuan_today": 0,
            "budget_yuan_daily": 20,
        },
        "s3": {
            "event_id": "e3",
            "agent_id": "content-bot",
            "agent_name": "内容 Agent",
            "type": "cost_report",
            "symptom": "over_budget",
            "error": "",
            "log_snippet": "tokens marketing-batch budget exceeded",
            "ts": "2026-06-28T00:00:00Z",
            "retry_webhook": "",
            "cost_yuan_today": 28.5,
            "budget_yuan_daily": 20,
        },
    }
    return {
        "trace_id": trace,
        "agent_id": events[scenario]["agent_id"],
        "scenario_id": scenario,
        "event_json": events[scenario],
        "llm_json": {
            "impact": "test",
            "hypothesis": ["h1"],
            "reasoning_chain": ["a", "b", "c"],
            "steps": [{"order": 1, "action": "wait", "command": "sleep", "risk": "low"}],
            "comms_draft": "draft",
            "retry_recommended": scenario == "s1",
        },
        "score_json": {"total": 87 if scenario == "s1" else 58, "grade": "executable" if scenario == "s1" else "escalate"},
    }


def test_knowledge_graph_builds_nodes():
    inc = _sample_incident()
    graph = build_knowledge_graph([inc])
    assert graph["stats"]["node_count"] >= 4
    types = {n["type"] for n in graph["nodes"]}
    assert "agent" in types and "incident" in types


def test_multi_hop_query():
    inc = _sample_incident()
    graph = build_knowledge_graph([inc])
    result = query_multi_hop(graph, "cs-bot")
    assert result["agent_id"] == "cs-bot"


def test_similar_incidents():
    a = _sample_incident("s1", "tr-a")
    b = _sample_incident("s1", "tr-b")
    b["event_json"]["log_snippet"] = "concurrent rate_limit 429"
    similar = find_similar_incidents(a, [a, b])
    assert len(similar) == 1
    assert similar[0]["trace_id"] == "tr-b"


def test_team_mode_s1_sub_agent():
    event = AgentEvent.model_validate(_sample_incident("s1")["event_json"])
    assert select_orchestration_mode(event, "cs_rate_limit") == "sub_agent"
    plan = build_team_plan("sub_agent", event, "cs_rate_limit")
    assert len(plan["team_agents"]) == 2


def test_team_mode_s3_agent_team():
    event = AgentEvent.model_validate(_sample_incident("s3")["event_json"])
    assert select_orchestration_mode(event, "cost_over_budget") == "agent_team"


@pytest.mark.asyncio
async def test_ultra_api_graph(client):
    await client.post("/admin/trigger/s1")
    resp = await client.get("/admin/ultra/graph")
    assert resp.status_code == 200
    assert resp.json()["stats"]["incidents"] >= 1


@pytest.mark.asyncio
async def test_ultra_what_if(client):
    trigger = await client.post("/admin/trigger/s1")
    trace_id = trigger.json()["trace_id"]
    resp = await client.post(
        f"/admin/ultra/incidents/{trace_id}/what-if",
        json={"changes": {"log_snippet": "concurrent=5 rate_limit recovered stable"}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "counterfactual_score" in data
    assert data["narrative"]


@pytest.mark.asyncio
async def test_ultra_team_plan_in_timeline(client):
    trigger = await client.post("/admin/trigger/s2")
    trace_id = trigger.json()["trace_id"]
    inc = await client.get(f"/admin/incidents/{trace_id}")
    types = [e["type"] for e in inc.json()["timeline_json"]]
    assert "team_orchestration" in types

    plan = await client.get(f"/admin/ultra/incidents/{trace_id}/team-plan")
    assert plan.json()["mode"] == "multi_agent"


@pytest.mark.asyncio
async def test_audit_log_api(client):
    await client.post("/admin/trigger/s1", headers={"X-Operator": "audit-test"})
    resp = await client.get("/admin/audit/log")
    assert resp.status_code == 200
    assert resp.json()["count"] >= 1
