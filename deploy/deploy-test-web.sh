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

SOURCE_ENV_FILE="$SHARED_REPO_ROOT/services/web/.env"
if [ ! -f "$SOURCE_ENV_FILE" ]; then
  echo "✗ services/web/.env 파일을 찾을 수 없습니다: $SOURCE_ENV_FILE"
  exit 1
fi

load_env_file() {
  local env_file="$1"

  if [ ! -f "$env_file" ]; then
    return 0
  fi

  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      ''|'#'*) continue ;;
    esac

    case "$line" in
      *=*)
        local key="${line%%=*}"
        local value="${line#*=}"
        ;;
      *)
        continue
        ;;
    esac

    case "$key" in
      ''|*[!A-Za-z0-9_]*)
        continue
        ;;
    esac

    printf -v "$key" '%s' "$value"
    export "$key"
  done < "$env_file"
}

PORT="${PORT:-3010}"
APP_HOST="${APP_HOST:-0.0.0.0}"
PM2_NAME="${PM2_NAME:-lawdigest-web}"
RUNTIME_ROOT="${RUNTIME_ROOT:-$SHARED_REPO_ROOT/.runtime/test-web}"
RELEASES_DIR="$RUNTIME_ROOT/releases"
CURRENT_LINK="$RUNTIME_ROOT/current"
TMP_LINK="$RUNTIME_ROOT/.current.tmp"

NEXT_PUBLIC_URL="${NEXT_PUBLIC_URL:-https://api.lawdigest.kr/}"
NEXT_PUBLIC_IMAGE_URL="${NEXT_PUBLIC_IMAGE_URL:-https://api.lawdigest.kr}"
NEXT_PUBLIC_HOSTNAME="${NEXT_PUBLIC_HOSTNAME:-api.lawdigest.kr}"
INTERNAL_API_ORIGIN="${INTERNAL_API_ORIGIN:-http://127.0.0.1:808}"

load_env_file "$SOURCE_ENV_FILE"
if [ -f "$TARGET_ROOT/.env.preview" ]; then
  # shellcheck disable=SC1090
  . "$TARGET_ROOT/.env.preview"
fi

load_env_file "$TARGET_WEB_DIR/.env.preview"

NEXT_PUBLIC_DOMAIN="${NEXT_PUBLIC_DOMAIN:-https://dev.lawdigest.kr}"

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
INTERNAL_API_ORIGIN="$INTERNAL_API_ORIGIN" \
NEXT_PUBLIC_DOMAIN="$NEXT_PUBLIC_DOMAIN" \
npm run build

echo "▶ release 디렉터리 생성"
mkdir -p "$RELEASE_DIR/services"

echo "▶ 산출물 복사"
cp -a "$TARGET_WEB_DIR" "$RELEASE_DIR/services/"

echo "▶ current 심링크 전환"
ln -sfn "$RELEASE_DIR" "$TMP_LINK"
mv -Tf "$TMP_LINK" "$CURRENT_LINK"

echo "▶ PM2 재기동"
if pm2 describe "$PM2_NAME" > /dev/null 2>&1; then
  pm2 delete "$PM2_NAME"
fi

cd "$CURRENT_LINK/services/web"
PORT="$PORT" \
HOSTNAME="$APP_HOST" \
NEXT_PUBLIC_URL="$NEXT_PUBLIC_URL" \
NEXT_PUBLIC_IMAGE_URL="$NEXT_PUBLIC_IMAGE_URL" \
NEXT_PUBLIC_HOSTNAME="$NEXT_PUBLIC_HOSTNAME" \
INTERNAL_API_ORIGIN="$INTERNAL_API_ORIGIN" \
NEXT_PUBLIC_DOMAIN="$NEXT_PUBLIC_DOMAIN" \
pm2 start npm --name "$PM2_NAME" -- run start
pm2 save

echo "✓ 배포 완료"
echo "  url: https://dev.lawdigest.kr"
echo "  runtime: $CURRENT_LINK"
