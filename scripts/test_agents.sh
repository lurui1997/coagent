#!/usr/bin/env bash
# 三 Agent simulate 模式接入 CoAgent 冒烟测试
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
BASE="${COAGENT_URL:-http://localhost:8000}"

echo "=== CoAgent Agent 接入测试 ==="
curl -sf "$BASE/health" >/dev/null || { echo "✗ CoAgent 未运行 ($BASE)"; exit 1; }
echo "✓ CoAgent healthy"

for agent in cs-bot rag-bot content-bot; do
  echo ""
  echo "--- $agent (simulate) ---"
  python3 -m agents.cli run "$agent" --mode simulate
done

echo ""
echo "=== 完成：请在控制台 Tab2 查看最新 trace ==="
