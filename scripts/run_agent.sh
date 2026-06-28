#!/usr/bin/env bash
# 运行本地 Claude Agent 并接入 CoAgent
# 用法: bash scripts/run_agent.sh cs-bot simulate
#       bash scripts/run_agent.sh rag-bot live --query "退货政策"
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
exec python3 -m agents.cli run "$@"
