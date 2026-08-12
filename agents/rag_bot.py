from __future__ import annotations

from app.config import settings

from agents.claude_runner import claude_print
from agents.coagent_client import CoAgentClient
from agents.kb_retrieval import build_retrieval_log, retrieve
from agents.scenario_events import build_empty_retrieval_event, load_scenario_event
from agents.telemetry import SimulateBundle, spans_from_event

AGENT_ID = "rag-bot"
AGENT_NAME = "RAG 客服 Agent"


class RAGBot:
    def __init__(self, client: CoAgentClient | None = None):
        self.client = client or CoAgentClient(settings.coagent_public_url)

    def build_simulate(self) -> SimulateBundle:
        event = load_scenario_event("s2")
        return SimulateBundle(event=event, spans=spans_from_event(event), agent_id=AGENT_ID)

    def run_simulate(self) -> dict:
        bundle = self.build_simulate()
        telemetry = self.client.export_traces(bundle.to_otlp(), operator="rag-bot/simulate")
        coagent = telemetry.get("incident") or {}
        return bundle.as_result(coagent, telemetry)

    def run_live(self, query: str) -> dict:
        result = retrieve(query)
        if result.is_empty:
            log = build_retrieval_log(query, result)
            event = build_empty_retrieval_event(
                AGENT_ID,
                AGENT_NAME,
                query=query,
                log_snippet=log,
            )
            spans = spans_from_event(event)
            telemetry = self.client.export_traces(
                SimulateBundle(event=event, spans=spans, agent_id=AGENT_ID, mode="live").to_otlp(),
                operator="rag-bot/live",
            )
            return {
                "agent": AGENT_ID,
                "mode": "live",
                "status": "run_fail",
                "symptom": "empty_retrieval",
                "chunks": 0,
                "max_score": result.max_score,
                "threshold": result.threshold,
                "coagent": telemetry.get("incident") or {},
                "telemetry": telemetry,
            }

        context = "\n".join(
            f"- [{h.entry['id']}] {h.entry['question']} (score={h.score}): {h.entry['answer']}"
            for h in result.hits
        )
        prompt = (
            "你是企业知识库 RAG 客服 Agent（rag-bot）。仅依据下列检索片段回答，"
            "若无依据请明确说明，不要编造政策。\n\n"
            f"检索片段：\n{context}\n\n用户问题：{query}"
        )
        claude = claude_print(prompt)
        if claude.returncode != 0:
            return {"agent": AGENT_ID, "mode": "live", "status": "error", "error": claude.combined[:500]}
        return {
            "agent": AGENT_ID,
            "mode": "live",
            "status": "ok",
            "chunks": len(result.hits),
            "max_score": result.max_score,
            "hit_ids": [h.entry["id"] for h in result.hits],
            "answer": claude.stdout.strip(),
        }
