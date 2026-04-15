#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REF_INPUT="${1:-main}"
DEV_WORKTREE_PATH="${DEV_WORKTREE_PATH:-$REPO_ROOT/.worktrees/dev-web-live}"
RUNTIME_ROOT="${RUNTIME_ROOT:-$REPO_ROOT/.runtime/dev-web}"
CURRENT_LINK="$RUNTIME_ROOT/current"
TMP_LINK="$RUNTIME_ROOT/.current.tmp"
PORT="${WEB_PORT:-3021}"
APP_HOST="${APP_HOST:-0.0.0.0}"
PM2_NAME="${PM2_NAME:-lawdigest-web-dev}"
NEXT_PUBLIC_URL="${NEXT_PUBLIC_URL:-https://api.lawdigest.kr/}"
NEXT_PUBLIC_IMAGE_URL="${NEXT_PUBLIC_IMAGE_URL:-https://api.lawdigest.kr}"
NEXT_PUBLIC_HOSTNAME="${NEXT_PUBLIC_HOSTNAME:-api.lawdigest.kr}"
INTERNAL_API_ORIGIN="${INTERNAL_API_ORIGIN:-http://127.0.0.1:808}"
NEXT_PUBLIC_DOMAIN="${NEXT_PUBLIC_DOMAIN:-https://dev.lawdigest.kr}"

load_ref() {
  local ref="$1"

  if git -C "$REPO_ROOT" rev-parse --verify "$ref" >/dev/null 2>&1; then
    printf '%s' "$ref"
    return 0
  fi

  if git -C "$REPO_ROOT" rev-parse --verify "origin/$ref" >/dev/null 2>&1; then
    printf '%s' "origin/$ref"
    return 0
  fi

  return 1
}

echo "▶ 개발용 웹 배포 시작 (next dev)"
echo "  repo: $REPO_ROOT"
echo "  ref input: $REF_INPUT"
echo "  worktree: $DEV_WORKTREE_PATH"
echo "  port: $PORT"
echo "  pm2: $PM2_NAME"
echo "  domain: $NEXT_PUBLIC_DOMAIN"

git -C "$REPO_ROOT" fetch origin --prune

RESOLVED_REF="$(load_ref "$REF_INPUT")" || {
  echo "✗ git ref를 찾을 수 없습니다: $REF_INPUT"
  exit 1
}

if [ ! -d "$DEV_WORKTREE_PATH/.git" ] && [ ! -f "$DEV_WORKTREE_PATH/.git" ]; then
  git -C "$REPO_ROOT" worktree add --detach "$DEV_WORKTREE_PATH" "$RESOLVED_REF"
else
  git -C "$DEV_WORKTREE_PATH" fetch origin --prune
  git -C "$DEV_WORKTREE_PATH" checkout --detach "$RESOLVED_REF"
fi

mkdir -p "$RUNTIME_ROOT"

TARGET_WEB_DIR="$DEV_WORKTREE_PATH/services/web"
if [ ! -d "$TARGET_WEB_DIR" ]; then
  echo "✗ services/web 디렉터리를 찾을 수 없습니다: $TARGET_WEB_DIR"
  exit 1
fi

echo "▶ 의존성 설치"
cd "$TARGET_WEB_DIR"
npm install

echo "▶ current 심링크 전환"
ln -sfn "$DEV_WORKTREE_PATH" "$TMP_LINK"
mv -Tf "$TMP_LINK" "$CURRENT_LINK"

echo "▶ PM2 개발 서버 재기동"
if pm2 describe "$PM2_NAME" > /dev/null 2>&1; then
  pm2 delete "$PM2_NAME"
fi

cd "$CURRENT_LINK/services/web"
NODE_ENV=development \
PORT="$PORT" \
HOSTNAME="$APP_HOST" \
NEXT_PUBLIC_URL="$NEXT_PUBLIC_URL" \
NEXT_PUBLIC_IMAGE_URL="$NEXT_PUBLIC_IMAGE_URL" \
NEXT_PUBLIC_HOSTNAME="$NEXT_PUBLIC_HOSTNAME" \
INTERNAL_API_ORIGIN="$INTERNAL_API_ORIGIN" \
NEXT_PUBLIC_DOMAIN="$NEXT_PUBLIC_DOMAIN" \
pm2 start npm --name "$PM2_NAME" -- run dev -- --hostname "$APP_HOST" --port "$PORT"
pm2 save

echo "✓ 개발모드 배포 완료"
echo "  ref: $RESOLVED_REF"
echo "  commit: $(git -C "$DEV_WORKTREE_PATH" rev-parse --short HEAD)"
echo "  runtime: $CURRENT_LINK"
echo "  url: $NEXT_PUBLIC_DOMAIN"
