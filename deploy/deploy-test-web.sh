#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKTREE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_ROOT="${1:-$WORKTREE_ROOT}"
COMMON_GIT_DIR="$(git -C "$TARGET_ROOT" rev-parse --git-common-dir)"
SHARED_REPO_ROOT="$(cd "$COMMON_GIT_DIR/.." && pwd)"

if [ ! -d "$TARGET_ROOT/.git" ] && [ ! -f "$TARGET_ROOT/.git" ]; then
  echo "✗ 유효한 git worktree 경로가 아닙니다: $TARGET_ROOT"
  exit 1
fi

TARGET_WEB_DIR="$TARGET_ROOT/services/web"
if [ ! -d "$TARGET_WEB_DIR" ]; then
  echo "✗ services/web 디렉터리를 찾을 수 없습니다: $TARGET_WEB_DIR"
  exit 1
fi

PORT="${PORT:-3010}"
APP_HOST="${APP_HOST:-0.0.0.0}"
PM2_NAME="${PM2_NAME:-lawdigest-web}"
RUNTIME_ROOT="${RUNTIME_ROOT:-$SHARED_REPO_ROOT/.runtime/test-web}"
RELEASES_DIR="$RUNTIME_ROOT/releases"
CURRENT_LINK="$RUNTIME_ROOT/current"
TMP_LINK="$RUNTIME_ROOT/.current.tmp"
STAGING_PORT="${STAGING_PORT:-$((PORT + 1000))}"
STAGING_PM2_NAME="${STAGING_PM2_NAME:-${PM2_NAME}-staging}"
HEALTHCHECK_PATH="${HEALTHCHECK_PATH:-/election}"

NEXT_PUBLIC_URL="${NEXT_PUBLIC_URL:-https://api.lawdigest.net/}"
NEXT_PUBLIC_IMAGE_URL="${NEXT_PUBLIC_IMAGE_URL:-https://api.lawdigest.net}"
NEXT_PUBLIC_HOSTNAME="${NEXT_PUBLIC_HOSTNAME:-api.lawdigest.net}"
NEXT_PUBLIC_DOMAIN="${NEXT_PUBLIC_DOMAIN:-https://dev.lawdigest.net}"

if [ -f "$TARGET_ROOT/.env.preview" ]; then
  # shellcheck disable=SC1090
  . "$TARGET_ROOT/.env.preview"
fi

PREVIOUS_RELEASE_DIR=""
if [ -e "$CURRENT_LINK" ]; then
  PREVIOUS_RELEASE_DIR="$(readlink -f "$CURRENT_LINK" 2>/dev/null || true)"
fi

pm2_delete_if_exists() {
  local process_name="$1"

  if pm2 describe "$process_name" > /dev/null 2>&1; then
    pm2 delete "$process_name" >/dev/null
  fi
}

start_pm2_from_release() {
  local process_name="$1"
  local port="$2"
  local release_dir="$3"

  cd "$release_dir/services/web"
  PORT="$port" \
  HOSTNAME="$APP_HOST" \
  NEXT_PUBLIC_URL="$NEXT_PUBLIC_URL" \
  NEXT_PUBLIC_IMAGE_URL="$NEXT_PUBLIC_IMAGE_URL" \
  NEXT_PUBLIC_HOSTNAME="$NEXT_PUBLIC_HOSTNAME" \
  NEXT_PUBLIC_DOMAIN="$NEXT_PUBLIC_DOMAIN" \
  pm2 start npm --name "$process_name" -- run start
}

check_health() {
  local port="$1"

  for _ in $(seq 1 30); do
    if curl -fsSI "http://127.0.0.1:${port}${HEALTHCHECK_PATH}" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done

  return 1
}

BRANCH_NAME="$(git -C "$TARGET_ROOT" branch --show-current)"
COMMIT_SHA="$(git -C "$TARGET_ROOT" rev-parse --short HEAD)"
RELEASE_ID="$(date +%Y%m%d%H%M%S)-${COMMIT_SHA}"
RELEASE_DIR="$RELEASES_DIR/$RELEASE_ID"

echo "▶ 테스트 배포 시작 (release/symlink)"
echo "  target: $TARGET_ROOT"
echo "  branch: $BRANCH_NAME"
echo "  commit: $COMMIT_SHA"
echo "  release: $RELEASE_ID"
echo "  port: $PORT"
echo "  pm2: $PM2_NAME"

mkdir -p "$RELEASES_DIR"

echo "▶ 의존성 설치"
cd "$TARGET_WEB_DIR"
npm install

echo "▶ 프로덕션 빌드"
NEXT_PUBLIC_URL="$NEXT_PUBLIC_URL" \
NEXT_PUBLIC_IMAGE_URL="$NEXT_PUBLIC_IMAGE_URL" \
NEXT_PUBLIC_HOSTNAME="$NEXT_PUBLIC_HOSTNAME" \
NEXT_PUBLIC_DOMAIN="$NEXT_PUBLIC_DOMAIN" \
npm run build

echo "▶ release 디렉터리 생성"
mkdir -p "$RELEASE_DIR/services"

echo "▶ 산출물 복사"
cp -a "$TARGET_WEB_DIR" "$RELEASE_DIR/services/"

echo "▶ staging PM2 기동"
pm2_delete_if_exists "$STAGING_PM2_NAME"
start_pm2_from_release "$STAGING_PM2_NAME" "$STAGING_PORT" "$RELEASE_DIR"

echo "▶ staging 헬스체크"
if ! check_health "$STAGING_PORT"; then
  echo "✗ staging 헬스체크 실패"
  pm2_delete_if_exists "$STAGING_PM2_NAME"
  exit 1
fi

echo "▶ live PM2 전환"
HAD_LIVE_PM2=0
if pm2 describe "$PM2_NAME" > /dev/null 2>&1; then
  HAD_LIVE_PM2=1
  pm2 delete "$PM2_NAME" >/dev/null
fi

if ! start_pm2_from_release "$PM2_NAME" "$PORT" "$RELEASE_DIR"; then
  echo "✗ live PM2 기동 실패"
  pm2_delete_if_exists "$PM2_NAME"
  if [ "$HAD_LIVE_PM2" -eq 1 ] && [ -n "$PREVIOUS_RELEASE_DIR" ] && [ -d "$PREVIOUS_RELEASE_DIR/services/web" ]; then
    echo "▶ 이전 release 복구"
    if ! start_pm2_from_release "$PM2_NAME" "$PORT" "$PREVIOUS_RELEASE_DIR"; then
      echo "✗ 이전 release 복구 실패"
      pm2_delete_if_exists "$STAGING_PM2_NAME"
      pm2 save
      exit 1
    fi
    if ! check_health "$PORT"; then
      echo "✗ 이전 release 복구 헬스체크 실패"
      pm2_delete_if_exists "$STAGING_PM2_NAME"
      pm2 save
      exit 1
    fi
  fi
  pm2_delete_if_exists "$STAGING_PM2_NAME"
  pm2 save
  exit 1
fi

echo "▶ live 헬스체크"
if ! check_health "$PORT"; then
  echo "✗ live 헬스체크 실패"
  pm2_delete_if_exists "$PM2_NAME"
  if [ "$HAD_LIVE_PM2" -eq 1 ] && [ -n "$PREVIOUS_RELEASE_DIR" ] && [ -d "$PREVIOUS_RELEASE_DIR/services/web" ]; then
    echo "▶ 이전 release 복구"
    if ! start_pm2_from_release "$PM2_NAME" "$PORT" "$PREVIOUS_RELEASE_DIR"; then
      echo "✗ 이전 release 복구 실패"
      pm2_delete_if_exists "$STAGING_PM2_NAME"
      pm2 save
      exit 1
    fi
    if ! check_health "$PORT"; then
      echo "✗ 이전 release 복구 헬스체크 실패"
      pm2_delete_if_exists "$STAGING_PM2_NAME"
      pm2 save
      exit 1
    fi
  fi
  pm2_delete_if_exists "$STAGING_PM2_NAME"
  pm2 save
  exit 1
fi

echo "▶ current 심링크 전환"
ln -sfn "$RELEASE_DIR" "$TMP_LINK"
mv -Tf "$TMP_LINK" "$CURRENT_LINK"

pm2_delete_if_exists "$STAGING_PM2_NAME"
pm2 save

echo "✓ 배포 완료"
echo "  url: https://dev.lawdigest.net"
echo "  runtime: $CURRENT_LINK"
