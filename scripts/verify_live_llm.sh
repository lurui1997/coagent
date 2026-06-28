#!/usr/bin/env bash
# 验证三场景真实 LLM 调用（需服务已启动且 MOCK_LLM=false）
set -euo pipefail
cd "$(dirname "$0")/.."

BASE="${BASE_URL:-http://127.0.0.1:8000}"
curl -sf "$BASE/health" > /dev/null

echo "=== CoAgent 真实 LLM 验证 ==="
echo "Base: $BASE"
echo ""

fail=0
for sid in s1 s2 s3; do
  echo "→ 触发 $sid ..."
  t0=$(date +%s)
  resp=$(curl -sf -X POST "$BASE/admin/trigger/$sid")
  trace=$(echo "$resp" | python3 -c "import sys,json; print(json.load(sys.stdin)['trace_id'])")
  t1=$(date +%s)
  inc=$(curl -sf "$BASE/admin/incidents/$trace")
  status=$(echo "$inc" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'])")
  model=$(echo "$inc" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('llm_model') or 'n/a')")
  score=$(echo "$inc" | python3 -c "import sys,json; d=json.load(sys.stdin); s=d.get('score_json') or {}; print(s.get('total','n/a'))")
  chain=$(echo "$inc" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len((d.get('llm_json') or {}).get('reasoning_chain') or []))")
  tools=$(echo "$inc" | python3 -c "import sys,json; d=json.load(sys.stdin); print(sum(1 for e in (d.get('timeline_json') or []) if e.get('type')=='tool_called'))")
  agent=$(echo "$inc" | python3 -c "import sys,json; d=json.load(sys.stdin); print(any(e.get('type')=='diagnostic_agent_started' for e in (d.get('timeline_json') or [])))")

  dur=$((t1 - t0))
  if [[ "$status" != "completed" || "$chain" -lt 3 ]]; then
    echo "  ✗ $sid failed status=$status chain=$chain (${dur}s)"
    fail=1
  else
    echo "  ✓ $sid trace=$trace model=$model score=$score chain=$chain tools=$tools diagnostic=$agent (${dur}s)"
  fi
  echo ""
done

if [[ "$fail" -ne 0 ]]; then
  exit 1
fi
echo "=== 全部场景真实 LLM 验证通过 ==="
