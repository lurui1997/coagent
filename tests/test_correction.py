import pytest


@pytest.mark.asyncio
async def test_correction_suggestions_s1(client):
    resp = await client.post("/admin/trigger/s1")
    trace_id = resp.json()["trace_id"]
    detail = await client.get(f"/admin/incidents/{trace_id}")
    suggestions = detail.json()["correction_suggestions"]
    assert len(suggestions) >= 1
    params = {s["param"] for s in suggestions}
    assert "concurrent" in params


@pytest.mark.asyncio
async def test_apply_correction(client):
    resp = await client.post("/admin/trigger/s1")
    trace_id = resp.json()["trace_id"]
    apply = await client.post(
        f"/admin/incidents/{trace_id}/apply-correction",
        headers={"X-Operator": "sre-bob"},
    )
    assert apply.status_code == 200
    data = apply.json()
    assert data["status"] == "ok"
    assert data["operator"] == "sre-bob"
    assert data["suggestions_applied"] >= 1

    export = await client.get("/admin/audit/export")
    record = next(r for r in export.json()["records"] if r["trace_id"] == trace_id)
    assert any(a["action_type"] == "correction_applied" for a in record["audit_actions"])


@pytest.mark.asyncio
async def test_correction_s3_model_suggestion(client):
    resp = await client.post("/admin/trigger/s3")
    trace_id = resp.json()["trace_id"]
    detail = await client.get(f"/admin/incidents/{trace_id}/corrections")
    params = {s["param"] for s in detail.json()["suggestions"]}
    assert "model" in params
    assert "max_tokens" in params
