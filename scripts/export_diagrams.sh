#!/usr/bin/env bash
# 导出架构 HTML → PNG / GIF
set -euo pipefail
cd "$(dirname "$0")/.."

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

cat > "$TMP_DIR/package.json" <<'EOF'
{"type":"module","private":true,"dependencies":{"playwright":"1.49.1"}}
EOF

echo "→ 安装 Playwright Chromium（首次较慢）..."
npm install --prefix "$TMP_DIR" --silent
"$TMP_DIR/node_modules/.bin/playwright" install chromium

echo "→ 导出架构图..."
export COAGENT_ROOT="$(pwd)"
cp scripts/export_diagrams.mjs "$TMP_DIR/export_diagrams.mjs"
node "$TMP_DIR/export_diagrams.mjs"

echo ""
echo "完成。产出位于 docs/diagrams/"
