#!/usr/bin/env bash
# CoAgent 15s 精简 Demo 录屏
set -euo pipefail
cd "$(dirname "$0")/.."

BASE_URL="${BASE_URL:-http://localhost:8000}"
export BASE_URL
export DEMO_TARGET_SEC="${DEMO_TARGET_SEC:-15}"

echo "=== CoAgent 15s Demo 录制 ==="
curl -sf "$BASE_URL/health" > /dev/null || {
  echo "请先启动: .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000"
  exit 1
}

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

cat > "$TMP_DIR/package.json" <<'EOF'
{"type":"module","private":true,"dependencies":{"playwright":"1.49.1"}}
EOF

echo "→ 安装 Playwright Chromium…"
npm install --prefix "$TMP_DIR" --silent
"$TMP_DIR/node_modules/.bin/playwright" install chromium

export COAGENT_ROOT="$(pwd)"
cp scripts/record_demo_15s.mjs "$TMP_DIR/record_demo_15s.mjs"
node "$TMP_DIR/record_demo_15s.mjs"

echo ""
echo "完成。视频位于 docs/demos/coagent-demo-15s-*.mp4"
