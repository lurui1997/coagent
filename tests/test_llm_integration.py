import json
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@pytest.mark.asyncio
async def test_admin_homepage(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    assert "CoAgent" in resp.text


@pytest.mark.asyncio
async def test_full_pipeline_mock(client):
    for scenario in ("s1", "s2", "s3"):
        payload = json.load(open(DATA_DIR / "scenarios" / f"{scenario}.json"))
        payload["event_id"] = f"evt-pipeline-{scenario}-{id(scenario)}"
        resp = await client.post("/events", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

        incident = await client.get(f"/admin/incidents/{data['trace_id']}")
        inc = incident.json()
        assert inc["status"] == "completed"
        assert inc["llm_json"] is not None
        assert inc["score_json"] is not None
        assert len(inc["timeline_json"]) >= 5


@pytest.mark.asyncio
async def test_demo_retry(client):
    resp = await client.post("/demo/retry/cs-bot")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["agent_id"] == "cs-bot"


@pytest.mark.asyncio
async def test_feedback_stats(client):
    trigger = await client.post("/admin/trigger/s1")
    trace_id = trigger.json()["trace_id"]

    await client.post(f"/admin/incidents/{trace_id}/feedback?rating=down")
    stats = await client.get("/admin/stats")
    assert stats.json()["thumbs_down"] >= 1


@pytest.mark.live_llm
@pytest.mark.asyncio
async def test_live_llm_s1(client):
    import os
    if not os.environ.get("LLM_API_KEY"):
        pytest.skip("LLM_API_KEY not set")

    from app.config import settings
    settings.mock_llm = False
    settings.llm_api_key = os.environ["LLM_API_KEY"]

    resp = await client.post("/admin/trigger/s1")
    data = resp.json()
    assert data["status"] == "ok"
    incident = await client.get(f"/admin/incidents/{data['trace_id']}")
    inc = incident.json()
    assert inc["llm_json"]["reasoning_chain"]
    assert len(inc["llm_json"]["reasoning_chain"]) >= 3
