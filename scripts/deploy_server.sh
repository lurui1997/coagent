#!/usr/bin/env bash
# 在服务器上执行：拉代码、装依赖、重启 uvicorn，并验证页面版本
set -euo pipefail

REPO_DIR="${COAGENT_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
BASE_URL="${COAGENT_URL:-http://127.0.0.1:8000}"
VENV="${COAGENT_VENV:-$REPO_DIR/.venv}"

cd "$REPO_DIR"
echo "=== CoAgent 部署: $REPO_DIR ==="

git pull origin main
# shellcheck disable=SC1091
source "$VENV/bin/activate"
pip install -r requirements.txt -q

pkill -f 'uvicorn app.main:app' 2>/dev/null || true
sleep 1
nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 >> coagent.log 2>&1 &
sleep 2

bash "$REPO_DIR/scripts/verify_deploy.sh" "$BASE_URL"
echo "=== 部署完成 ==="
