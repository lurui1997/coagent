#!/usr/bin/env bash
# CoAgent 完整 Demo 录屏 — 三 Tab + S1/S2/S3 + 审计反馈
set -euo pipefail
cd "$(dirname "$0")/.."

RECORDER_PORT="${RECORDER_PORT:-8010}"
USE_ISOLATED="${USE_ISOLATED:-1}"
BASE_URL="${BASE_URL:-}"
RECORDER_PID=""
RECORDER_DB="coagent-recorder-${RECORDER_PORT}.db"

cleanup() {
  if [[ -n "${RECORDER_PID}" ]]; then
    kill "${RECORDER_PID}" 2>/dev/null || true
    wait "${RECORDER_PID}" 2>/dev/null || true
  fi
}

if [[ -z "${BASE_URL}" && "${USE_ISOLATED}" == "1" ]]; then
  BASE_URL="http://127.0.0.1:${RECORDER_PORT}"
  rm -f "${RECORDER_DB}"
  echo "→ 启动隔离录制服务 (MOCK_LLM=true) @ ${BASE_URL}"
  DATABASE_PATH="${RECORDER_DB}" MOCK_LLM=true DEMO_MODE=true DIAGNOSTIC_AGENT=true \
    .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port "${RECORDER_PORT}" &
  RECORDER_PID=$!
  trap cleanup EXIT
  for _ in $(seq 1 40); do
    if curl -sf "${BASE_URL}/health" > /dev/null; then break; fi
    sleep 0.5
  done
  curl -sf "${BASE_URL}/health" > /dev/null || {
    echo "✗ 录制服务启动失败"
    exit 1
  }
elif [[ -z "${BASE_URL}" ]]; then
  BASE_URL="http://localhost:8000"
fi

export BASE_URL
echo "=== CoAgent 完整 Demo 录制 ==="
echo "Base URL: ${BASE_URL}"

curl -sf "${BASE_URL}/health" > /dev/null || {
  echo "请先启动: MOCK_LLM=true DEMO_MODE=true uvicorn app.main:app --port 8000"
  exit 1
}

TMP_DIR="$(mktemp -d)"
trap 'cleanup; rm -rf "$TMP_DIR"' EXIT

cat > "$TMP_DIR/package.json" <<'EOF'
{"type":"module","private":true,"dependencies":{"playwright":"1.49.1"}}
EOF

echo "→ 安装 Playwright Chromium（首次较慢）..."
npm install --prefix "$TMP_DIR" --silent
"$TMP_DIR/node_modules/.bin/playwright" install chromium

echo "→ 开始录制（约 2–4 分钟）..."
export COAGENT_ROOT="$(pwd)"
cp scripts/record_demo.mjs "$TMP_DIR/record_demo.mjs"
node "$TMP_DIR/record_demo.mjs"

echo ""
echo "完成。视频位于 docs/demos/coagent-demo-*.mp4"
