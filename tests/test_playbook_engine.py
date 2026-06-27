import json
from pathlib import Path

import pytest

from app.models.event import AgentEvent
from app.playbooks.engine import PlaybookEngine
from app.router import route_scenario


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def test_router_s1():
    assert route_scenario("run_fail", "rate_limit") == "cs_rate_limit"


def test_router_s2():
    assert route_scenario("run_fail", "empty_retrieval") == "rag_empty_retrieval"


def test_router_s3():
    assert route_scenario("cost_report", "over_budget") == "cost_over_budget"


def test_router_unknown():
    assert route_scenario("unknown", "symptom") is None


def test_playbook_engine_loads_all():
    engine = PlaybookEngine(DATA_DIR / "ops_playbooks.json")
    assert set(engine.all_ids()) == {"cs_rate_limit", "rag_empty_retrieval", "cost_over_budget"}


@pytest.mark.asyncio
async def test_playbook_run_tools():
    engine = PlaybookEngine(DATA_DIR / "ops_playbooks.json")
    with open(DATA_DIR / "scenarios" / "s1.json") as f:
        event = AgentEvent.model_validate(json.load(f))
    results = await engine.run_tools("cs_rate_limit", event)
    assert len(results) == 3
    assert all(r["success"] for r in results)
    assert results[0]["tool"] == "query_agent_metrics"


def test_playbook_build_messages():
    engine = PlaybookEngine(DATA_DIR / "ops_playbooks.json")
    with open(DATA_DIR / "scenarios" / "s1.json") as f:
        event = AgentEvent.model_validate(json.load(f))
    msgs = engine.build_llm_messages("cs_rate_limit", event, [])
    assert msgs[0]["role"] == "system"
    assert "429" in msgs[1]["content"] or "rate_limit" in msgs[1]["content"]
