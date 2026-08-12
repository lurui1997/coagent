#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export DEMO_MODE=true
export PYTHONPATH="$ROOT"
# Unit/integration tests stub LLMClient in-process; live_llm needs a real key.
exec "$ROOT/.venv/bin/python3" -m pytest tests/ -m "not live_llm" "$@"
