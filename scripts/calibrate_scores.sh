#!/usr/bin/env bash
set -euo pipefail

SCENARIO="${1:-s1}"
RUNS="${2:-1}"
BASE_URL="${BASE_URL:-http://localhost:8000}"
OUT_DIR="data/calibration"
mkdir -p "$OUT_DIR"

scores=()
grades=()

for i in $(seq 1 "$RUNS"); do
  # Use unique event_id to avoid idempotency
  result=$(curl -sf -X POST "$BASE_URL/events" \
    -H "Content-Type: application/json" \
    -d @"data/scenarios/${SCENARIO}.json" | python3 -c "
import json,sys
d=json.load(sys.stdin)
print(d.get('trace_id',''))
" 2>/dev/null || echo "")

  if [ -z "$result" ]; then
    echo "Run $i: trigger failed (is server running?)"
    continue
  fi

  trace_id="$result"
  sleep 2
  score=$(curl -sf "$BASE_URL/admin/incidents/$trace_id" | python3 -c "
import json,sys
d=json.load(sys.stdin)
s=d.get('score_json') or {}
print(s.get('total','?'), s.get('grade','?'))
")
  echo "Run $i: trace=$trace_id score=$score"
  scores+=("$score")
done

python3 -c "
import json
scores = '''${scores[*]}'''.split()
print(json.dumps({'scenario': '$SCENARIO', 'runs': $RUNS, 'results': scores}, indent=2))
" > "$OUT_DIR/${SCENARIO}.json"

echo "Calibration saved to $OUT_DIR/${SCENARIO}.json"
