import pytest


@pytest.mark.asyncio
async def test_replay_readonly(client):
    trigger = await client.post("/admin/trigger/s2")
    trace_id = trigger.json()["trace_id"]

    replay = await client.post(f"/admin/replay/{trace_id}")
    assert replay.status_code == 200
    assert replay.json()["status"] == "ok"

    incident = await client.get(f"/admin/incidents/{trace_id}")
    data = incident.json()
    assert data["llm_json"] is not None
    assert data["score_json"] is not None
    assert len(data["timeline_json"]) > 0


@pytest.mark.asyncio
async def test_replay_not_found(client):
    resp = await client.post("/admin/replay/tr-nonexistent")
    assert resp.status_code == 404
