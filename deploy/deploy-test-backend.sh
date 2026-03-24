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

SOURCE_ENV_FILE="$SHARED_REPO_ROOT/services/backend/.env"
if [ ! -f "$SOURCE_ENV_FILE" ]; then
  echo "✗ services/backend/.env 파일을 찾을 수 없습니다: $SOURCE_ENV_FILE"
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

HOST_PORT="${PORT:-808}"
CONTAINER_NAME="${CONTAINER_NAME:-lawdigest-backend-test}"
IMAGE_NAME="${IMAGE_NAME:-lawdigest-backend-test}"
DOCKER_NETWORK="${DOCKER_NETWORK:-law_prod_network}"
ACTIVE="${ACTIVE:-test}"

BRANCH_NAME="$(git -C "$TARGET_ROOT" branch --show-current)"
COMMIT_SHA="$(git -C "$TARGET_ROOT" rev-parse --short HEAD)"

echo "▶ 테스트 백엔드 배포 시작 (docker)"
echo "  target: $TARGET_ROOT"
echo "  branch: $BRANCH_NAME"
echo "  commit: $COMMIT_SHA"
echo "  host port: $HOST_PORT"
echo "  container: $CONTAINER_NAME"
echo "  image: $IMAGE_NAME"
echo "  network: $DOCKER_NETWORK"
echo "  active profile: $ACTIVE"

echo "▶ Gradle 빌드"
cd "$TARGET_BACKEND_DIR"
./gradlew clean bootJar

JAR_SOURCE="$(find "$TARGET_BACKEND_DIR/build/libs" -maxdepth 1 -type f -name '*.jar' ! -name '*-plain.jar' | sort | tail -n 1)"
if [ -z "$JAR_SOURCE" ]; then
  echo "✗ bootJar 산출물을 찾지 못했습니다: $TARGET_BACKEND_DIR/build/libs"
  exit 1
fi

echo "▶ Docker 이미지 빌드"
docker build -t "$IMAGE_NAME" -f Dockerfile .

echo "▶ 기존 컨테이너 정리"
docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true

echo "▶ 테스트 백엔드 컨테이너 실행"
docker run -d \
  --name "$CONTAINER_NAME" \
  --network "$DOCKER_NETWORK" \
  --env-file "$SOURCE_ENV_FILE" \
  -e ACTIVE="$ACTIVE" \
  -p "$HOST_PORT:8080" \
  -v "$SHARED_REPO_ROOT/.runtime/test-backend/logs:/logs" \
  -v /usr/share/zoneinfo/Asia/Seoul:/etc/localtime:ro \
  "$IMAGE_NAME" >/dev/null

echo "▶ 기동 확인"
for _ in $(seq 1 30); do
  if curl -sSI "http://127.0.0.1:$HOST_PORT/" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

if ! curl -sSI "http://127.0.0.1:$HOST_PORT/" >/dev/null 2>&1; then
  echo "✗ 백엔드 응답 확인 실패"
  docker logs --tail 100 "$CONTAINER_NAME" || true
  exit 1
fi

echo "✓ 배포 완료"
echo "  url: http://127.0.0.1:$HOST_PORT"
echo "  runtime: docker container $CONTAINER_NAME"
