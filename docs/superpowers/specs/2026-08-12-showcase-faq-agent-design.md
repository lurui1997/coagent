# Showcase FAQ Agent — Design Spec

**Date:** 2026-08-12  
**Status:** Accepted (user skipped remaining confirmations; recommended defaults applied)  
**Decisions:** [../showcase/faq-agent-decisions.md](../../showcase/faq-agent-decisions.md)

## Summary

Ship an independent `showcase/faq_agent` package: enterprise FAQ RAG with real DeepSeek calls, quantitative metrics dashboard, and OTLP promotion into CoAgent for empty-retrieval quality incidents. Remove production `MOCK_LLM` path.

## Architecture

```text
Browser → /showcase/faq (dashboard + /ask)
                ↓
         FAQAgent (retrieve → DeepSeek → metrics)
                ↓ empty retrieval
         TelemetryService /v1/traces → Detector → Orchestrator
```

## Components

- `retrieval.py` — keyword FAQ retrieval over sample corpus  
- `llm.py` — real chat completions only  
- `metrics.py` — SQLite ask_events + summary rates  
- `telemetry_export.py` — OTLP JSON for empty_retrieval  
- `app.py` — FastAPI router mounted in `app.main`

## Testing

- Non-live tests stub `LLMClient` / `answer_with_llm` in-process  
- `live_llm` requires real `LLM_API_KEY`
