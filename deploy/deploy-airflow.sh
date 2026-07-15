#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_ROOT="${1:-$REPO_ROOT}"
COMPOSE_FILE="$TARGET_ROOT/infra/airflow/docker-compose.yaml"
AIRFLOW_SKIP_GIT_PULL="${AIRFLOW_SKIP_GIT_PULL:-false}"
AIRFLOW_FULL_STACK="${AIRFLOW_FULL_STACK:-false}"
AIRFLOW_BUILD_IMAGE="${AIRFLOW_BUILD_IMAGE:-false}"

if [ ! -d "$TARGET_ROOT/.git" ] && [ ! -f "$TARGET_ROOT/.git" ]; then
  echo "✗ 유효한 git worktree 경로가 아닙니다: $TARGET_ROOT"
  exit 1
fi

if [ ! -f "$COMPOSE_FILE" ]; then
  echo "✗ Airflow compose 파일을 찾을 수 없습니다: $COMPOSE_FILE"
  exit 1
fi

COMMON_GIT_DIR="$(git -C "$TARGET_ROOT" rev-parse --path-format=absolute --git-common-dir)"
SHARED_REPO_ROOT="$(cd "$COMMON_GIT_DIR/.." && pwd)"
COMPOSE_ENV_FILE="${AIRFLOW_COMPOSE_ENV_FILE:-$SHARED_REPO_ROOT/infra/airflow/.env}"

export LAWDIGEST_PROJECT_DIR="${LAWDIGEST_PROJECT_DIR:-$TARGET_ROOT}"
export LAWDIGEST_DATA_ENV_FILE="${LAWDIGEST_DATA_ENV_FILE:-$SHARED_REPO_ROOT/services/data/.env}"

if [ ! -f "$LAWDIGEST_DATA_ENV_FILE" ]; then
  echo "✗ Airflow data 환경 파일을 찾을 수 없습니다: $LAWDIGEST_DATA_ENV_FILE"
  exit 1
fi

COMPOSE_ARGS=(-f "$COMPOSE_FILE" --project-directory "$TARGET_ROOT/infra/airflow")
if [ -f "$COMPOSE_ENV_FILE" ]; then
  COMPOSE_ARGS+=(--env-file "$COMPOSE_ENV_FILE")
fi

echo "▶ Airflow 코드 동기화 시작"
echo "  target: $TARGET_ROOT"
echo "  branch: $(git -C "$TARGET_ROOT" branch --show-current)"
echo "  before: $(git -C "$TARGET_ROOT" rev-parse --short HEAD)"

if [ "$AIRFLOW_SKIP_GIT_PULL" = "true" ]; then
  echo "▶ 지정 커밋 사용 (git pull 생략)"
else
  echo "▶ 최신 커밋 pull"
  git -C "$TARGET_ROOT" pull --ff-only
fi

echo "▶ Airflow 컨테이너 재기동"
SERVICES=(airflow-webserver airflow-scheduler)
UP_ARGS=(-d --no-deps --force-recreate)

if [ "$AIRFLOW_FULL_STACK" = "true" ]; then
  SERVICES+=(airflow-worker airflow-triggerer airflow-log-pruner)
  UP_ARGS=(-d --force-recreate)
fi

if [ "$AIRFLOW_BUILD_IMAGE" = "true" ]; then
  UP_ARGS+=(--build)
fi

docker compose "${COMPOSE_ARGS[@]}" up "${UP_ARGS[@]}" "${SERVICES[@]}"

echo "▶ Airflow API 서버 준비 대기"
for _ in $(seq 1 60); do
  WEB_CONTAINER="$(docker compose "${COMPOSE_ARGS[@]}" ps -q airflow-webserver)"
  if [ -n "$WEB_CONTAINER" ]; then
    WEB_STATUS="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$WEB_CONTAINER")"
    if [ "$WEB_STATUS" = "healthy" ] || [ "$WEB_STATUS" = "running" ]; then
      break
    fi
    if [ "$WEB_STATUS" = "unhealthy" ] || [ "$WEB_STATUS" = "exited" ]; then
      echo "✗ Airflow API 서버 상태가 비정상입니다: $WEB_STATUS"
      docker compose "${COMPOSE_ARGS[@]}" logs --tail 100 airflow-webserver
      exit 1
    fi
  fi
  sleep 5
done

WEB_CONTAINER="$(docker compose "${COMPOSE_ARGS[@]}" ps -q airflow-webserver)"
if [ -z "$WEB_CONTAINER" ]; then
  echo "✗ Airflow API 서버 컨테이너를 찾을 수 없습니다."
  exit 1
fi

WEB_STATUS="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$WEB_CONTAINER")"
if [ "$WEB_STATUS" != "healthy" ] && [ "$WEB_STATUS" != "running" ]; then
  echo "✗ Airflow API 서버가 제한 시간 안에 준비되지 않았습니다: $WEB_STATUS"
  docker compose "${COMPOSE_ARGS[@]}" logs --tail 100 airflow-webserver
  exit 1
fi

echo "▶ DAG import 오류 확인"
docker compose "${COMPOSE_ARGS[@]}" exec -T airflow-webserver airflow dags list-import-errors

echo "▶ DAG 목록 확인"
docker compose "${COMPOSE_ARGS[@]}" exec -T airflow-webserver airflow dags list | sed -n '1,40p'

echo "▶ Airflow 서비스 상태"
docker compose "${COMPOSE_ARGS[@]}" ps

echo "✓ Airflow 동기화 완료"
echo "  commit: $(git -C "$TARGET_ROOT" rev-parse --short HEAD)"
echo "  project: $LAWDIGEST_PROJECT_DIR"
