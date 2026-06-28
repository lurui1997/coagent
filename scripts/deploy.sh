#!/usr/bin/env bash
#
# deploy.sh — 拉取最新代码并在本地重新部署 CoAgent
#
# 流程：
#   1. 暂存本地改动并 fast-forward 拉取 origin/main
#   2. 依赖有变化时自动 pip install
#   3. 重启 systemd 后端服务 (coagent.service)
#   4. 同步静态官网到 nginx 目录（含 localhost -> /coagent 链接改写）
#   5. 校验 nginx 配置并 reload
#   6. 健康检查（后端 + 经 nginx 的官网/管理台）
#
# 用法：
#   bash scripts/deploy.sh              # 正常部署
#   bash scripts/deploy.sh --no-pull    # 跳过 git 拉取，仅重新部署当前代码
#   BRANCH=main bash scripts/deploy.sh  # 指定分支（默认 main）
#
set -euo pipefail

# ---- 配置（可用环境变量覆盖）----
REPO_DIR="${REPO_DIR:-/root/github/coagent}"
BRANCH="${BRANCH:-main}"
SERVICE="${SERVICE:-coagent.service}"
SITE_DIR="${SITE_DIR:-/usr/share/nginx/coagent-site}"
NGINX_USER="${NGINX_USER:-nginx}"
BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8000}"
NGINX_HOST="${NGINX_HOST:-aikipedia.cn}"
PIP="${PIP:-/root/.local/bin/python3.12 -m pip}"

NO_PULL=0
[ "${1:-}" = "--no-pull" ] && NO_PULL=1

log()  { printf '\033[1;34m[deploy]\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m  ✓\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m  ! \033[0m%s\n' "$*"; }
die()  { printf '\033[1;31m[deploy] ✗ %s\033[0m\n' "$*" >&2; exit 1; }

cd "$REPO_DIR" || die "找不到仓库目录: $REPO_DIR"

# ---- 1. 拉取最新代码 ----
if [ "$NO_PULL" -eq 1 ]; then
  log "跳过 git 拉取 (--no-pull)"
else
  log "拉取最新代码 (origin/$BRANCH)"
  OLD_HEAD="$(git rev-parse HEAD)"

  # 暂存未提交改动，避免 pull 失败
  STASHED=0
  if ! git diff --quiet || ! git diff --cached --quiet; then
    warn "检测到本地未提交改动，先 stash 暂存"
    # 兼容老版本 git（1.8.x 无 stash push，使用 stash save）
    if git stash push -u -m "deploy.sh auto-stash" >/dev/null 2>&1; then
      :
    else
      git stash save -u "deploy.sh auto-stash" >/dev/null
    fi
    STASHED=1
  fi

  git fetch origin "$BRANCH"
  if git merge-base --is-ancestor HEAD "origin/$BRANCH"; then
    git merge --ff-only "origin/$BRANCH"
  else
    [ "$STASHED" -eq 1 ] && git stash pop >/dev/null 2>&1 || true
    die "无法 fast-forward：本地有偏离 origin/$BRANCH 的提交，请手动处理"
  fi

  if [ "$STASHED" -eq 1 ]; then
    if git stash pop >/dev/null 2>&1; then
      ok "已恢复暂存的本地改动"
    else
      warn "stash pop 冲突，本地改动仍保留在 stash 中（git stash list 查看）"
    fi
  fi

  NEW_HEAD="$(git rev-parse HEAD)"
  if [ "$OLD_HEAD" = "$NEW_HEAD" ]; then
    ok "已是最新：$(git rev-parse --short HEAD)"
  else
    ok "更新 ${OLD_HEAD:0:7} -> ${NEW_HEAD:0:7}"
    # 依赖变化时重新安装
    if git diff --name-only "$OLD_HEAD" "$NEW_HEAD" | grep -q '^requirements.txt$'; then
      log "requirements.txt 有变化，安装依赖"
      $PIP install -r requirements.txt
      ok "依赖已更新"
    fi
  fi
fi

# ---- 2. 重启后端服务 ----
log "重启后端服务 ($SERVICE)"
systemctl restart "$SERVICE"
sleep 2
systemctl is-active --quiet "$SERVICE" || {
  systemctl status "$SERVICE" --no-pager -n 15 || true
  die "后端服务启动失败"
}
ok "$SERVICE active"

# ---- 3. 同步静态官网 ----
log "同步官网到 $SITE_DIR"
mkdir -p "$SITE_DIR"
# -T 风格的内容拷贝（绕过 cp 别名的交互提示）
cp -rf "$REPO_DIR"/website/. "$SITE_DIR"/
# 把官网中指向本地后端的链接改写为 /coagent 路由
sed -i 's#http://localhost:8000/docs#/coagent/docs#g; s#http://localhost:8000/#/coagent/#g' "$SITE_DIR/index.html"
chown -R "$NGINX_USER":"$NGINX_USER" "$SITE_DIR" 2>/dev/null || true
chmod -R a+rX "$SITE_DIR" || true
LEFT="$(grep -c 'localhost:8000' "$SITE_DIR/index.html" 2>/dev/null || true)"
LEFT="$(printf '%s' "$LEFT" | tr -d '[:space:]')"
if [ "${LEFT:-0}" = "0" ]; then
  ok "官网已同步，链接改写完成"
else
  warn "index.html 仍有 ${LEFT} 处 localhost:8000 引用"
fi

# ---- 4. 校验并 reload nginx ----
log "校验 nginx 配置"
if nginx -t 2>/dev/null; then
  systemctl reload nginx
  ok "nginx 已 reload"
else
  nginx -t || true
  die "nginx 配置校验失败，已跳过 reload"
fi

# ---- 5. 健康检查 ----
log "健康检查"
FAIL=0
check() { # name  curl-args...
  local name="$1"; shift
  local code; code="$(curl -s -o /dev/null -w '%{http_code}' "$@" || echo 000)"
  if [ "$code" = "200" ]; then ok "$name ($code)"; else warn "$name 期望 200 实际 $code"; FAIL=1; fi
}
check "后端 /health"          "$BACKEND_URL/health"
check "后端 /"               "$BACKEND_URL/"
check "官网 / (nginx)"        -H "Host: $NGINX_HOST" "http://127.0.0.1/"
check "管理台 /?tab=1 (nginx)" -H "Host: $NGINX_HOST" "http://127.0.0.1/?tab=1"
check "管理台 /coagent/ (nginx)" -H "Host: $NGINX_HOST" "http://127.0.0.1/coagent/"

echo
if [ "${FAIL:-0}" -eq 0 ]; then
  log "部署完成 ✅  当前版本 $(git rev-parse --short HEAD) — $(git log -1 --pretty=%s)"
else
  die "部署完成但部分健康检查未通过，请检查上面的告警"
fi
