# Showcase FAQ Agent
#
# Local:
#   set -a && source .env && set +a
#   uvicorn app.main:app --reload --port 8000
#   open http://localhost:8000/showcase/faq
#
# Demo empty-retrieval incident:
#   curl -X POST 'http://localhost:8000/showcase/faq/demo/empty-retrieval'
#
# Requires LLM_API_KEY (DeepSeek). No mock LLM path.

See also:
- docs/showcase/faq-agent-decisions.md
- docs/showcase/faq-agent-status.md
