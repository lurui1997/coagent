import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any

from app.config import settings
from app.db import (
    find_duplicate_event,
    get_incident,
    insert_incident,
    new_trace_id,
    update_incident,
    upsert_agent_stats,
)
from app.llm.client import LLMClient
from app.models.event import AgentEvent
from app.models.llm_output import LLMOutput
from app.playbooks.engine import PlaybookEngine
from app.router import route_scenario
from app.scoring.scorer import compute_score
from app.sse import sse_manager

logger = logging.getLogger(__name__)

SCENARIO_MAP = {"s1": "cs_rate_limit", "s2": "rag_empty_retrieval", "s3": "cost_over_budget"}


class Orchestrator:
    def __init__(self):
        self.engine = PlaybookEngine()
        self.llm = LLMClient()

    async def process_event(self, event: AgentEvent, scenario_id: str | None = None) -> dict[str, Any]:
        existing = find_duplicate_event(event.event_id)
        if existing:
            return {"status": "duplicate", "trace_id": existing}

        playbook_id = route_scenario(event.type, event.symptom)
        if not playbook_id:
            raise ValueError(f"No route for ({event.type}, {event.symptom})")

        if not scenario_id:
            for sid, pid in SCENARIO_MAP.items():
                if pid == playbook_id:
                    scenario_id = sid
                    break
            scenario_id = scenario_id or playbook_id

        trace_id = new_trace_id()
        incident_id = insert_incident(trace_id, event.event_id, event.agent_id, scenario_id, event.model_dump())
        timeline: list[dict] = []
        start_ms = time.time()

        async def record(event_type: str, payload: dict) -> None:
            entry = {"type": event_type, "payload": payload}
            timeline.append(entry)
            await sse_manager.emit(trace_id, event_type, payload)

        try:
            await asyncio.wait_for(
                self._run_pipeline(event, playbook_id, trace_id, record),
                timeout=settings.pipeline_timeout_s,
            )
            duration_ms = int((time.time() - start_ms) * 1000)
            update_incident(trace_id, status="completed", timeline_json=timeline, duration_ms=duration_ms)
            upsert_agent_stats(event.agent_id, event.type, event.cost_yuan_today)
            return {"status": "ok", "trace_id": trace_id, "incident_id": incident_id}
        except Exception as e:
            logger.exception("Pipeline failed for %s", trace_id)
            await record("incident_failed", {"error": str(e)})
            update_incident(trace_id, status="failed", timeline_json=timeline)
            return {"status": "failed", "trace_id": trace_id, "error": str(e)}

    async def _run_pipeline(
        self,
        event: AgentEvent,
        playbook_id: str,
        trace_id: str,
        record: Any,
    ) -> None:
        from app.channels.feishu_im import send_incident_card

        await record("incident_started", {"event_id": event.event_id, "agent_id": event.agent_id})

        tool_results = []
        try:
            tool_results = await asyncio.wait_for(
                self.engine.run_tools(playbook_id, event),
                timeout=settings.tool_timeout_s,
            )
        except asyncio.TimeoutError:
            pb = self.engine.get(playbook_id)
            tool_results = [
                {"tool": t, "result": pb["tool_mocks"].get(t, {}), "success": False, "degraded": True}
                for t in pb["required_tools"]
            ]

        for tr in tool_results:
            await record("tool_called", tr)

        messages = self.engine.build_llm_messages(playbook_id, event, tool_results)
        llm_output: LLMOutput | None = None
        try:
            llm_output = await asyncio.wait_for(
                self.llm.generate_with_retry(messages, playbook_id),
                timeout=settings.llm_timeout_s,
            )
        except Exception as e:
            raise RuntimeError(f"LLM failed: {e}") from e

        await record("llm_reasoning", {"reasoning_chain": llm_output.reasoning_chain})
        llm_dict = llm_output.model_dump()
        await record("llm_result", llm_dict)
        update_incident(trace_id, llm_json=llm_dict)

        playbook = self.engine.get_playbook_for_scoring(playbook_id)
        score = compute_score(event, llm_output, playbook, tool_results)
        await record("score_computed", score)
        update_incident(trace_id, score_json=score)

        if playbook_id == "cs_rate_limit":
            try:
                msg_id = await asyncio.wait_for(
                    send_incident_card(event, llm_output, score),
                    timeout=settings.feishu_timeout_s,
                )
                await record("channel_sync", {"channel": "feishu", "msg_id": msg_id or "mock"})
                if msg_id:
                    update_incident(trace_id, feishu_msg_id=msg_id)
            except Exception as e:
                logger.warning("Feishu failed (L2): %s", e)
                await record("channel_sync", {"channel": "feishu", "status": "failed", "error": str(e)})

        await record("incident_completed", {"trace_id": trace_id})

    async def replay(self, trace_id: str) -> dict[str, Any]:
        incident = get_incident(trace_id)
        if not incident:
            raise ValueError(f"Incident {trace_id} not found")
        timeline = incident.get("timeline_json") or []
        await sse_manager.replay(trace_id, timeline)
        return {"status": "ok", "trace_id": trace_id}

    def load_scenario(self, scenario_id: str) -> AgentEvent:
        path = settings.data_dir / "scenarios" / f"{scenario_id}.json"
        with open(path, encoding="utf-8") as f:
            return AgentEvent.model_validate(json.load(f))


orchestrator = Orchestrator()
