#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export MOCK_LLM=true
export DEMO_MODE=true
export PYTHONPATH="$ROOT"
exec "$ROOT/.venv/bin/python3" -m pytest tests/ -m "not live_llm" "$@"
