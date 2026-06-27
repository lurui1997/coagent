#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"

echo "=== CoAgent Demo Script ==="
echo "Base URL: $BASE_URL"

curl -sf "$BASE_URL/health" > /dev/null && echo "✓ Server healthy" || { echo "✗ Server not reachable"; exit 1; }

for s in s1 s2 s3; do
  echo ""
  echo "--- Triggering $s ---"
  result=$(curl -sf -X POST "$BASE_URL/admin/trigger/$s")
  echo "$result" | python3 -m json.tool
  trace=$(echo "$result" | python3 -c "import json,sys; print(json.load(sys.stdin).get('trace_id',''))")
  sleep 2
  if [ -n "$trace" ]; then
    curl -sf "$BASE_URL/admin/incidents/$trace" | python3 -c "
import json,sys
d=json.load(sys.stdin)
sc=d.get('score_json') or {}
print(f\"  Score: {sc.get('total')} {sc.get('grade')} ({sc.get('labels',{}).get('grade_display','')})\")
"
  fi
done

echo ""
echo "=== Demo complete ==="
