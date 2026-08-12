"""Audit detail navigation from action log."""

import pytest


@pytest.mark.asyncio
async def test_audit_detail_renders_above_log_for_trace(client):
    """详情跳转后应在日志列表上方展示故障详情，避免「点了没跳」的感知。"""
    trigger = await client.post("/admin/trigger/s1", headers={"X-Operator": "audit-nav"})
    assert trigger.status_code == 200
    trace_id = trigger.json()["trace_id"]

    page = await client.get(f"/?tab=3&trace={trace_id}")
    assert page.status_code == 200
    html = page.text

    detail_at = html.find('id="audit-detail-panel"')
    log_at = html.find('id="audit-log-section"')
    assert detail_at != -1, "expected audit detail panel for trace"
    assert log_at != -1, "expected audit log section"
    assert detail_at < log_at, "detail panel must appear above action log"
    assert trace_id in html
    assert "故障详情" in html


@pytest.mark.asyncio
async def test_audit_detail_missing_trace_shows_notice(client):
    page = await client.get("/?tab=3&trace=tr-does-not-exist")
    assert page.status_code == 200
    assert 'id="audit-detail-missing"' in page.text
    assert "未找到" in page.text
