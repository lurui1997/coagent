import json
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@pytest.mark.asyncio
async def test_duplicate_event_id(client):
    with open(DATA_DIR / "scenarios" / "s1.json") as f:
        payload = json.load(f)
    payload["event_id"] = "evt-idem-test-001"

    r1 = await client.post("/events", json=payload)
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["status"] == "ok"
    trace1 = data1["trace_id"]

    r2 = await client.post("/events", json=payload)
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["status"] == "duplicate"
    assert data2["trace_id"] == trace1


@pytest.mark.asyncio
async def test_trigger_idempotency(client):
    r1 = await client.post("/admin/trigger/s1")
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["status"] == "ok"

    r2 = await client.post("/admin/trigger/s1")
    data2 = r2.json()
    assert data2["status"] == "duplicate"
    assert data2["trace_id"] == data1["trace_id"]
