#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKTREE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_ROOT="${1:-$WORKTREE_ROOT}"

if [ ! -d "$TARGET_ROOT" ]; then
  echo "✗ 대상 경로가 존재하지 않습니다: $TARGET_ROOT"
  exit 1
fi

COMMON_GIT_DIR="$(git -C "$TARGET_ROOT" rev-parse --git-common-dir)"
SHARED_REPO_ROOT="$(cd "$COMMON_GIT_DIR/.." && pwd)"

if [ ! -d "$TARGET_ROOT/.git" ] && [ ! -f "$TARGET_ROOT/.git" ]; then
  echo "✗ 유효한 git worktree 경로가 아닙니다: $TARGET_ROOT"
  exit 1
fi

TARGET_BACKEND_DIR="$TARGET_ROOT/services/backend"
if [ ! -d "$TARGET_BACKEND_DIR" ]; then
  echo "✗ services/backend 디렉터리를 찾을 수 없습니다: $TARGET_BACKEND_DIR"
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

load_env_file "$TARGET_ROOT/.env.preview"
load_env_file "$TARGET_BACKEND_DIR/.env.preview"

PORT="${PORT:-18080}"
PM2_NAME="${PM2_NAME:-lawdigest-backend-test}"
RUNTIME_ROOT="${RUNTIME_ROOT:-$SHARED_REPO_ROOT/.runtime/test-backend}"
RELEASES_DIR="$RUNTIME_ROOT/releases"
CURRENT_LINK="$RUNTIME_ROOT/current"
TMP_LINK="$RUNTIME_ROOT/.current.tmp"
ACTIVE="${ACTIVE:-test}"

BRANCH_NAME="$(git -C "$TARGET_ROOT" branch --show-current)"
COMMIT_SHA="$(git -C "$TARGET_ROOT" rev-parse --short HEAD)"
RELEASE_ID="$(date +%Y%m%d%H%M%S)-${COMMIT_SHA}"
RELEASE_DIR="$RELEASES_DIR/$RELEASE_ID"
BACKEND_ENV_FILE="$RELEASE_DIR/backend.env"
LAUNCHER_FILE="$RELEASE_DIR/run.sh"
JAR_FILE="$RELEASE_DIR/app.jar"

echo "▶ 테스트 백엔드 배포 시작 (release/symlink)"
echo "  target: $TARGET_ROOT"
echo "  branch: $BRANCH_NAME"
echo "  commit: $COMMIT_SHA"
echo "  release: $RELEASE_ID"
echo "  port: $PORT"
echo "  pm2: $PM2_NAME"
echo "  active profile: $ACTIVE"

mkdir -p "$RELEASES_DIR"

echo "▶ Gradle 빌드"
cd "$TARGET_BACKEND_DIR"
./gradlew clean bootJar

JAR_SOURCE="$(find "$TARGET_BACKEND_DIR/build/libs" -maxdepth 1 -type f -name '*.jar' ! -name '*-plain.jar' | sort | tail -n 1)"
if [ -z "$JAR_SOURCE" ]; then
  echo "✗ bootJar 산출물을 찾지 못했습니다: $TARGET_BACKEND_DIR/build/libs"
  exit 1
fi

echo "▶ release 디렉터리 생성"
mkdir -p "$RELEASE_DIR"

echo "▶ 실행 파일 복사"
cp "$JAR_SOURCE" "$JAR_FILE"

if [ -f "$TARGET_BACKEND_DIR/.env" ]; then
  cp "$TARGET_BACKEND_DIR/.env" "$BACKEND_ENV_FILE"
else
  : > "$BACKEND_ENV_FILE"
fi

{
  printf '\n'
  printf 'ACTIVE=%s\n' "$ACTIVE"
  printf 'SERVER_PORT=%s\n' "$PORT"
  printf 'DB_HOSTNAME=127.0.0.1\n'
  printf 'BIN_LOG_HOST=127.0.0.1\n'
  printf 'ELASTIC_CACHE_HOST=127.0.0.1\n'
} >> "$BACKEND_ENV_FILE"

cat > "$LAUNCHER_FILE" <<'EOF'
#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/backend.env"

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

load_env_file "$ENV_FILE"

JAVA_BIN="java"
if [ -n "${JAVA_HOME:-}" ] && [ -x "$JAVA_HOME/bin/java" ]; then
  JAVA_BIN="$JAVA_HOME/bin/java"
fi

exec "$JAVA_BIN" -jar "$SCRIPT_DIR/app.jar"
EOF
chmod +x "$LAUNCHER_FILE"

echo "▶ current 심링크 전환"
ln -sfn "$RELEASE_DIR" "$TMP_LINK"
mv -Tf "$TMP_LINK" "$CURRENT_LINK"

echo "▶ PM2 재기동"
if pm2 describe "$PM2_NAME" > /dev/null 2>&1; then
  pm2 delete "$PM2_NAME"
fi

cd "$CURRENT_LINK"
pm2 start "$LAUNCHER_FILE" --name "$PM2_NAME"
pm2 save

echo "✓ 배포 완료"
echo "  url: http://127.0.0.1:$PORT"
echo "  runtime: $CURRENT_LINK"
