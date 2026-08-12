"""Pipeline failure recording should surface actionable errors."""

import asyncio

import pytest

from app.config import settings
from app.models.event import AgentEvent
from app.orchestrator import Orchestrator


@pytest.mark.asyncio
async def test_pipeline_timeout_records_nonempty_error(monkeypatch, s1_event=None):
    from pathlib import Path
    import json

    data_dir = Path(__file__).resolve().parent.parent / "data"
    with open(data_dir / "scenarios" / "s1.json") as f:
        event = AgentEvent.model_validate(json.load(f))

    monkeypatch.setattr(settings, "pipeline_timeout_s", 0.05)
    orch = Orchestrator()

    async def hang(*_args, **_kwargs):
        await asyncio.sleep(10)

    monkeypatch.setattr(orch, "_run_pipeline", hang)

    prepared = orch.prepare_incident(event, scenario_id="s1", operator="test")
    assert prepared["status"] == "prepared"

    result = await orch.run_pipeline_bg(
        prepared["trace_id"],
        prepared["incident_id"],
        event,
        prepared["playbook_id"],
        operator="test",
    )
    assert result["status"] == "failed"
    assert result["error"]
    assert "timeout" in result["error"].lower() or "timed out" in result["error"].lower()

    from app.db import get_incident

    inc = get_incident(prepared["trace_id"])
    assert inc["status"] == "failed"
    failed = next(e for e in (inc["timeline_json"] or []) if e["type"] == "incident_failed")
    assert failed["payload"]["error"]
    assert failed["payload"].get("error_type") == "TimeoutError"
