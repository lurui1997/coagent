#!/usr/bin/env bash
# CoAgent 答辩 Demo 录屏 — 自动走查三 Tab + S1/S2/S3
set -euo pipefail
cd "$(dirname "$0")/.."

BASE_URL="${BASE_URL:-http://localhost:8000}"
export BASE_URL

echo "=== CoAgent Demo 录制 ==="
curl -sf "$BASE_URL/health" > /dev/null || {
  echo "请先启动: MOCK_LLM=true DEMO_MODE=true uvicorn app.main:app --port 8000"
  exit 1
}

# 本地临时安装 playwright（不写入 package.json）
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

cat > "$TMP_DIR/package.json" <<'EOF'
{"type":"module","private":true,"dependencies":{"playwright":"1.49.1"}}
EOF

echo "→ 安装 Playwright Chromium（首次较慢）..."
npm install --prefix "$TMP_DIR" --silent
"$TMP_DIR/node_modules/.bin/playwright" install chromium

echo "→ 开始录制..."
export COAGENT_ROOT="$(pwd)"
cp scripts/record_demo.mjs "$TMP_DIR/record_demo.mjs"
node "$TMP_DIR/record_demo.mjs"

echo ""
echo "完成。视频位于 docs/demos/"
