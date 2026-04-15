#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RUNTIME_ROOT="${RUNTIME_ROOT:-$REPO_ROOT/.runtime/dev-web}"
CURRENT_LINK="$RUNTIME_ROOT/current"
NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
WEB_PORT="${WEB_PORT:-3021}"
APP_HOST="${APP_HOST:-0.0.0.0}"
PM2_NAME="${PM2_NAME:-lawdigest-web-dev}"
NEXT_PUBLIC_URL="${NEXT_PUBLIC_URL:-https://api.lawdigest.kr/}"
NEXT_PUBLIC_IMAGE_URL="${NEXT_PUBLIC_IMAGE_URL:-https://api.lawdigest.kr}"
NEXT_PUBLIC_HOSTNAME="${NEXT_PUBLIC_HOSTNAME:-api.lawdigest.kr}"
INTERNAL_API_ORIGIN="${INTERNAL_API_ORIGIN:-http://127.0.0.1:808}"
NEXT_PUBLIC_DOMAIN="${NEXT_PUBLIC_DOMAIN:-https://dev.lawdigest.kr}"
QUIET=0

if [ "${1:-}" = "--quiet" ]; then
  QUIET=1
fi

log() {
  if [ "$QUIET" -eq 0 ]; then
    echo "$@"
  fi
}

if ! command -v node >/dev/null 2>&1 && [ -s "$NVM_DIR/nvm.sh" ]; then
  # shellcheck disable=SC1090
  . "$NVM_DIR/nvm.sh"
fi

NODE_BIN="$(command -v node || true)"
NPM_BIN="$(command -v npm || true)"
PM2_BIN="$(command -v pm2 || true)"

if [ -z "$NODE_BIN" ] || [ -z "$NPM_BIN" ] || [ -z "$PM2_BIN" ]; then
  log "✗ node/npm/pm2 경로를 찾지 못해 dev 웹 복구를 중단합니다"
  exit 1
fi

if [ ! -e "$CURRENT_LINK" ]; then
  log "↷ current 심링크가 없어 dev 웹 복구를 건너뜁니다: $CURRENT_LINK"
  exit 0
fi

TARGET_WEB_DIR="$CURRENT_LINK/services/web"
if [ ! -d "$TARGET_WEB_DIR" ]; then
  log "↷ services/web 디렉터리가 없어 dev 웹 복구를 건너뜁니다: $TARGET_WEB_DIR"
  exit 0
fi

TARGET_REALPATH="$(realpath "$TARGET_WEB_DIR")"

CURRENT_STATE="$(
  "$PM2_BIN" jlist | "$NODE_BIN" -e '
let buf = "";
process.stdin.on("data", (chunk) => { buf += chunk; });
process.stdin.on("end", () => {
  const name = process.argv[1];
  const apps = JSON.parse(buf);
  const app = apps.find((entry) => entry.name === name);
  if (!app) {
    process.exit(2);
  }
  const status = app.pm2_env?.status ?? "";
  const cwd = app.pm2_env?.pm_cwd ?? app.pm2_env?.cwd ?? "";
  const pid = String(app.pid ?? 0);
  process.stdout.write([status, cwd, pid].join("\t"));
});' "$PM2_NAME" 2>/dev/null || true
)"

if [ -n "$CURRENT_STATE" ]; then
  IFS=$'\t' read -r CURRENT_STATUS CURRENT_CWD CURRENT_PID <<< "$CURRENT_STATE"
  CURRENT_CWD_REALPATH="$(realpath -m "$CURRENT_CWD")"

  if [ "$CURRENT_STATUS" = "online" ] && [ "$CURRENT_CWD_REALPATH" = "$TARGET_REALPATH" ] && [ "${CURRENT_PID:-0}" != "0" ]; then
    log "✓ PM2 개발 서버가 이미 정상 상태입니다"
    "$PM2_BIN" save >/dev/null
    exit 0
  fi
fi

if "$PM2_BIN" describe "$PM2_NAME" >/dev/null 2>&1; then
  log "▶ 기존 PM2 프로세스 정리"
  "$PM2_BIN" delete "$PM2_NAME" >/dev/null
fi

log "▶ PM2 개발 서버 복구"
NODE_ENV=development \
PORT="$WEB_PORT" \
HOSTNAME="$APP_HOST" \
NEXT_PUBLIC_URL="$NEXT_PUBLIC_URL" \
NEXT_PUBLIC_IMAGE_URL="$NEXT_PUBLIC_IMAGE_URL" \
NEXT_PUBLIC_HOSTNAME="$NEXT_PUBLIC_HOSTNAME" \
INTERNAL_API_ORIGIN="$INTERNAL_API_ORIGIN" \
NEXT_PUBLIC_DOMAIN="$NEXT_PUBLIC_DOMAIN" \
"$PM2_BIN" start "$NPM_BIN" \
  --name "$PM2_NAME" \
  --cwd "$TARGET_WEB_DIR" \
  --update-env \
  -- run dev -- --hostname "$APP_HOST" --port "$WEB_PORT" >/dev/null

"$PM2_BIN" save >/dev/null
log "✓ PM2 개발 서버 복구 완료"
