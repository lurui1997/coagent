import json

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_sse_stream_replays_full_timeline(client):
    trigger = await client.post("/admin/trigger/s2")
    assert trigger.status_code == 200
    trace_id = trigger.json()["trace_id"]

    async with client.stream("GET", f"/admin/incidents/{trace_id}/stream") as resp:
        assert resp.status_code == 200
        body = ""
        async for chunk in resp.aiter_text():
            body += chunk

    events = []
    for block in body.split("\n\n"):
        for line in block.split("\n"):
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))

    types = [e["type"] for e in events]
    assert "incident_started" in types
    assert types.count("tool_called") == 3
    assert "llm_reasoning" in types
    assert "score_computed" in types
    assert "incident_completed" in types
    assert len(types) >= 8
