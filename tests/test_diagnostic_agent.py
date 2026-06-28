import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from app.config import settings
from app.diagnostic_agent import DiagnosticAgent
from app.llm.client import LLMClient
from app.models.event import AgentEvent
from app.playbooks.engine import PlaybookEngine

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture
def s1_event() -> AgentEvent:
    with open(DATA_DIR / "scenarios" / "s1.json") as f:
        return AgentEvent.model_validate(json.load(f))


@pytest.mark.asyncio
async def test_diagnostic_agent_calls_all_tools(s1_event, monkeypatch):
    monkeypatch.setattr(settings, "mock_llm", True)
    engine = PlaybookEngine(DATA_DIR / "ops_playbooks.json")
    agent = DiagnosticAgent(engine, LLMClient())
    timeline: list[dict] = []

    async def record(event_type: str, payload: dict) -> None:
        timeline.append({"type": event_type, "payload": payload})

    tool_results, llm_output, model = await agent.run(s1_event, "cs_rate_limit", record)

    assert len(tool_results) == 3
    assert all(r["success"] for r in tool_results)
    assert llm_output.impact
    assert len(llm_output.reasoning_chain) >= 3

    types = [e["type"] for e in timeline]
    assert "diagnostic_agent_started" in types
    assert types.count("tool_called") == 3
    assert types.count("agent_thought") >= 3


@pytest.mark.asyncio
async def test_diagnostic_agent_legacy_fallback_in_orchestrator(s1_event, monkeypatch):
    from app.orchestrator import Orchestrator

    monkeypatch.setattr(settings, "mock_llm", True)
    monkeypatch.setattr(settings, "diagnostic_agent", True)

    orch = Orchestrator()
    orch.engine = PlaybookEngine(DATA_DIR / "ops_playbooks.json")

    async def boom(*_args, **_kwargs):
        raise RuntimeError("react broken")

    orch.llm.generate_with_retry = AsyncMock(side_effect=boom)

    timeline: list[dict] = []

    async def record(event_type: str, payload: dict) -> None:
        timeline.append({"type": event_type, "payload": payload})

    with pytest.raises(RuntimeError, match="LLM failed"):
        await orch._run_legacy_llm_pipeline(s1_event, "cs_rate_limit", record)

    types = [e["type"] for e in timeline]
    assert types.count("tool_called") == 3
