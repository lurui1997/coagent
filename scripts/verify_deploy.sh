#!/usr/bin/env bash
# 验证线上/本地 CoAgent 部署：HTML 版本、CSS 可访问、样式类存在
set -euo pipefail
BASE="${1:-http://www.aikipedia.cn}"

echo "=== CoAgent 部署检查: $BASE ==="

html=$(curl -sf --max-time 20 "${BASE%/}/?tab=1")
css_path=$(echo "$html" | sed -n 's/.*href="\([^"]*style\.css[^"]*\)".*/\1/p' | head -1)
static_v=$(echo "$html" | sed -n 's/.*content="\([0-9]*\)".*/\1/p' | head -1 || true)

if echo "$html" | grep -qE 'Hackathon Demo|Demo 控制|Hackathon 演示'; then
  echo "⚠ HTML 仍为旧版（含 Hackathon/Demo 文案），请 git pull 并重启 uvicorn"
elif ! echo "$html" | grep -q 'coagent-static-v'; then
  echo "⚠ HTML 缺少 static_v 版本标记，静态资源可能未带 ?v= 缓存破坏"
else
  echo "✓ HTML 为企业版文案"
fi

if [ -z "$css_path" ]; then
  echo "✗ 未找到 style.css 链接"
  exit 1
fi

if ! echo "$css_path" | grep -q '?v='; then
  echo "⚠ HTML 中 style.css 未带 ?v= 版本号，浏览器可能命中旧 CSS 缓存"
fi

if [[ "$css_path" != /* ]]; then
  css_url="$css_path"
else
  css_url="${BASE%/}$css_path"
fi

echo "→ CSS: $css_url"
code=$(curl -sf -o /tmp/coagent-check.css -w '%{http_code}' --max-time 20 "$css_url")
[ "$code" = "200" ] || { echo "✗ CSS HTTP $code"; exit 1; }

bare_code=$(curl -sf -o /dev/null -w '%{http_code}|%{redirect_url}' --max-time 10 "${BASE%/}/static/style.css" 2>/dev/null || echo "000|")
if echo "$bare_code" | grep -q '^302|.*style\.css?v='; then
  echo "✓ 无版本号 /static/style.css 会 302 到带 ?v= 的 URL"
elif echo "$bare_code" | grep -q '^200|'; then
  echo "⚠ /static/style.css 无版本号仍返回 200，请确认已部署最新 main.py"
fi

if grep -q '\.pitch-hero' /tmp/coagent-check.css && grep -q '\.pitch-narrative' /tmp/coagent-check.css; then
  echo "✓ CSS 含 pitch 布局规则 ($(wc -c </tmp/coagent-check.css) bytes)"
else
  echo "✗ CSS 缺少 pitch 样式，可能部署了旧 static"
  exit 1
fi

curl -sf --max-time 10 "${BASE%/}/health" >/dev/null && echo "✓ /health OK" || echo "⚠ /health 不可达"

echo "=== 检查完成 ==="
