from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_showcase_dashboard(client):
    resp = await client.get("/showcase/faq/")
    assert resp.status_code == 200
    assert "Showcase FAQ Agent" in resp.text


@pytest.mark.asyncio
async def test_showcase_empty_retrieval_promotes_incident(client, monkeypatch, tmp_path):
    from showcase.faq_agent.app import _agent
    from showcase.faq_agent.metrics import MetricsStore

    store = MetricsStore(tmp_path / "m.db")
    _agent.metrics = store

    resp = await client.post(
        "/showcase/faq/ask",
        json={
            "query": "完全不存在的冷门政策 xyz-999",
            "force_empty": True,
            "allow_answer_on_empty": False,
            "promote": True,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["empty_retrieval"] is True
    assert data["incident"]
    assert data["incident"].get("trace_id")
    assert data["status"] == "empty_retrieval"

    body = store.summary()
    assert body["ask_count"] >= 1
    assert body["empty_retrieval_rate"] > 0
    assert body["incident_promotions"] >= 1


@pytest.mark.asyncio
async def test_showcase_happy_path_with_stubbed_llm(client, monkeypatch, tmp_path):
    from showcase.faq_agent.app import _agent
    from showcase.faq_agent.metrics import MetricsStore

    _agent.metrics = MetricsStore(tmp_path / "m2.db")

    async def fake_llm(*, query: str, context: str):
        return {
            "answer": "7 天无理由退货（测试桩）。",
            "prompt_tokens": 10,
            "completion_tokens": 8,
            "model": "stub-model",
            "raw": {},
        }

    monkeypatch.setattr("showcase.faq_agent.agent.answer_with_llm", fake_llm)

    resp = await client.post(
        "/showcase/faq/ask",
        json={"query": "退货政策是什么", "force_empty": False, "promote": False},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["empty_retrieval"] is False
    assert "退货" in data["answer"]
    assert data["hits"]
