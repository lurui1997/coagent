#!/usr/bin/env bash
# 验证线上/本地 CoAgent 部署：HTML 版本、CSS 可访问、样式类存在
set -euo pipefail
BASE="${1:-http://www.aikipedia.cn}"

echo "=== CoAgent 部署检查: $BASE ==="

html=$(curl -sf --max-time 20 "${BASE%/}/?tab=1")
css_path=$(echo "$html" | sed -n 's/.*href="\([^"]*style\.css[^"]*\)".*/\1/p' | head -1)
static_v=$(echo "$html" | sed -n 's/.*content="\([0-9]*\)".*/\1/p' | head -1 || true)

if echo "$html" | grep -q 'Hackathon Demo'; then
  echo "⚠ HTML 仍为旧版（含 Hackathon Demo），请 git pull 并重启 uvicorn"
else
  echo "✓ HTML 为企业版文案"
fi

if [ -z "$css_path" ]; then
  echo "✗ 未找到 style.css 链接"
  exit 1
fi

if [[ "$css_path" != /* ]]; then
  css_url="$css_path"
else
  css_url="${BASE%/}$css_path"
fi

echo "→ CSS: $css_url"
code=$(curl -sf -o /tmp/coagent-check.css -w '%{http_code}' --max-time 20 "$css_url")
[ "$code" = "200" ] || { echo "✗ CSS HTTP $code"; exit 1; }

if grep -q '\.pitch-hero' /tmp/coagent-check.css && grep -q '\.pitch-narrative' /tmp/coagent-check.css; then
  echo "✓ CSS 含 pitch 布局规则 ($(wc -c </tmp/coagent-check.css) bytes)"
else
  echo "✗ CSS 缺少 pitch 样式，可能部署了旧 static"
  exit 1
fi

curl -sf --max-time 10 "${BASE%/}/health" >/dev/null && echo "✓ /health OK" || echo "⚠ /health 不可达"

echo "=== 检查完成 ==="
