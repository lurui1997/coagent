import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_list_agents():
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/agents")
    assert resp.status_code == 200
    assert set(resp.json()["agents"]) == {"cs-bot", "rag-bot", "content-bot"}


@pytest.mark.asyncio
async def test_run_agent_simulate_cs_bot():
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/agents/cs-bot/run",
            json={"mode": "simulate"},
            headers={"X-Operator": "pytest"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent"] == "cs-bot"
    assert data["coagent"]["status"] in ("ok", "duplicate")
    assert data["coagent"].get("trace_id")


@pytest.mark.asyncio
async def test_run_agent_simulate_rag_and_content():
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for agent_id in ("rag-bot", "content-bot"):
            resp = await client.post(f"/agents/{agent_id}/run", json={"mode": "simulate"})
            assert resp.status_code == 200
            assert resp.json()["coagent"].get("trace_id")


@pytest.mark.asyncio
async def test_rag_bot_live_empty_retrieval(monkeypatch):
    from agents.rag_bot import RAGBot
    from app.main import app

    def fake_live(self, query: str):
        return {
            "agent": "rag-bot",
            "mode": "live",
            "status": "run_fail",
            "symptom": "empty_retrieval",
            "coagent": {"status": "ok", "trace_id": "tr-test-rag"},
        }

    monkeypatch.setattr(RAGBot, "run_live", fake_live)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/agents/rag-bot/run",
            json={"mode": "live", "query": "完全不存在的冷门问题 xyz"},
        )
    assert resp.status_code == 200
    assert resp.json()["symptom"] == "empty_retrieval"


@pytest.mark.asyncio
async def test_cs_bot_retry(monkeypatch):
    from agents.claude_runner import ClaudeResult
    from app.main import app

    monkeypatch.setattr(
        "agents.cs_bot.claude_print",
        lambda prompt: ClaudeResult(0, "服务已恢复", ""),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/agents/retry/cs-bot")
    assert resp.status_code == 200
    assert resp.json()["agent"] == "cs-bot"
    assert resp.json()["status"] == "ok"
