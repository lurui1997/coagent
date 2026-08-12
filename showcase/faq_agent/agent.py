from __future__ import annotations

import time
from typing import Any

from showcase.faq_agent.llm import answer_with_llm
from showcase.faq_agent.metrics import MetricsStore
from showcase.faq_agent.retrieval import retrieve
from showcase.faq_agent.telemetry_export import build_empty_retrieval_otlp

# ~¥0.001 / 1k tokens rough showcase estimate (not billing-grade)
_COST_PER_1K = 0.001


class FAQAgent:
    def __init__(self, metrics: MetricsStore | None = None):
        self.metrics = metrics or MetricsStore()

    async def ask(
        self,
        query: str,
        *,
        force_empty: bool = False,
        allow_answer_on_empty: bool = False,
        promote: bool = True,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        retrieval = retrieve(query, force_empty=force_empty)
        empty = retrieval.is_empty
        hallucination_risk = False
        incident: dict[str, Any] | None = None
        answer = ""
        prompt_tokens = 0
        completion_tokens = 0
        status = "ok"
        model = None

        if empty:
            status = "empty_retrieval"
            if promote:
                from app.telemetry.service import telemetry_service

                otlp = build_empty_retrieval_otlp(query=query)
                ingest = await telemetry_service.ingest_otlp_json(
                    otlp, promote=True, operator="showcase-faq-agent"
                )
                incident = ingest.incident
            if allow_answer_on_empty:
                # Explicit bad-path for demo: answer without evidence → risk flag
                hallucination_risk = True
                llm = await answer_with_llm(query=query, context="（无检索结果）")
                answer = llm["answer"]
                prompt_tokens = llm["prompt_tokens"]
                completion_tokens = llm["completion_tokens"]
                model = llm["model"]
                status = "hallucination_risk"
            else:
                answer = "知识库未检索到足够依据，我无法回答该问题。请换个问法或联系人工客服。"
        else:
            context = "\n".join(
                f"- [{h.entry['id']}] {h.entry['question']} (score={h.score:.2f}): {h.entry['answer']}"
                for h in retrieval.hits
            )
            llm = await answer_with_llm(query=query, context=context)
            answer = llm["answer"]
            prompt_tokens = llm["prompt_tokens"]
            completion_tokens = llm["completion_tokens"]
            model = llm["model"]

        latency_ms = int((time.perf_counter() - started) * 1000)
        est_cost = ((prompt_tokens + completion_tokens) / 1000.0) * _COST_PER_1K
        self.metrics.record(
            {
                "query": query,
                "empty_retrieval": empty,
                "hallucination_risk": hallucination_risk,
                "latency_ms": latency_ms,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "est_cost_yuan": est_cost,
                "incident_promoted": bool(incident and incident.get("trace_id")),
                "incident_trace_id": (incident or {}).get("trace_id"),
                "status": status,
            }
        )
        return {
            "agent": "showcase-faq-agent",
            "query": query,
            "answer": answer,
            "empty_retrieval": empty,
            "hallucination_risk": hallucination_risk,
            "hits": [
                {"id": h.entry["id"], "question": h.entry["question"], "score": h.score}
                for h in retrieval.hits
            ],
            "latency_ms": latency_ms,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "est_cost_yuan": round(est_cost, 6),
            "model": model,
            "incident": incident,
            "status": status,
        }
