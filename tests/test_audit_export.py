import json
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@pytest.mark.asyncio
async def test_audit_export_json(client):
    payload = json.load(open(DATA_DIR / "scenarios" / "s1.json"))
    payload["event_id"] = f"evt-audit-{id(payload)}"
    trigger = await client.post("/events", json=payload, headers={"X-Operator": "ops-alice"})
    trace_id = trigger.json()["trace_id"]

    export = await client.get("/admin/audit/export")
    assert export.status_code == 200
    data = export.json()
    assert data["count"] >= 1
    record = next(r for r in data["records"] if r["trace_id"] == trace_id)
    assert record["operator"] == "ops-alice"
    assert record["score_total"] is not None


@pytest.mark.asyncio
async def test_audit_export_csv(client):
    resp = await client.get("/admin/audit/export?format=csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers.get("content-type", "")
    body = resp.text
    assert "trace_id" in body
    assert "operator" in body


@pytest.mark.asyncio
async def test_operator_on_trigger(client):
    resp = await client.post("/admin/trigger/s1", headers={"X-Operator": "demo-user"})
    assert resp.status_code == 200
    trace_id = resp.json()["trace_id"]
    incident = await client.get(f"/admin/incidents/{trace_id}")
    assert incident.json()["operator"] == "demo-user"


@pytest.mark.asyncio
async def test_feedback_records_audit(client):
    trigger = await client.post("/admin/trigger/s2", headers={"X-Operator": "reviewer"})
    trace_id = trigger.json()["trace_id"]
    await client.post(
        f"/admin/incidents/{trace_id}/feedback?rating=up",
        headers={"X-Operator": "reviewer"},
    )
    export = await client.get("/admin/audit/export")
    record = next(r for r in export.json()["records"] if r["trace_id"] == trace_id)
    action_types = [a["action_type"] for a in record["audit_actions"]]
    assert "feedback" in action_types
