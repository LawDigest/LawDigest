#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_ROOT="${1:-$REPO_ROOT}"
COMPOSE_FILE="$TARGET_ROOT/infra/airflow/docker-compose.yaml"

if [ ! -d "$TARGET_ROOT/.git" ] && [ ! -f "$TARGET_ROOT/.git" ]; then
  echo "✗ 유효한 git worktree 경로가 아닙니다: $TARGET_ROOT"
  exit 1
fi

if [ ! -f "$COMPOSE_FILE" ]; then
  echo "✗ Airflow compose 파일을 찾을 수 없습니다: $COMPOSE_FILE"
  exit 1
fi

WEB_CONTAINER="airflow-airflow-webserver-1"
SCHEDULER_CONTAINER="airflow-airflow-scheduler-1"

echo "▶ Airflow 코드 동기화 시작"
echo "  target: $TARGET_ROOT"
echo "  branch: $(git -C "$TARGET_ROOT" branch --show-current)"
echo "  before: $(git -C "$TARGET_ROOT" rev-parse --short HEAD)"

echo "▶ 최신 커밋 pull"
git -C "$TARGET_ROOT" pull --ff-only

echo "▶ Airflow 컨테이너 재기동"
docker compose -f "$COMPOSE_FILE" up -d --no-deps --force-recreate airflow-webserver airflow-scheduler

echo "▶ DAG import 오류 확인"
docker exec "$WEB_CONTAINER" airflow dags list-import-errors || true

echo "▶ DAG 목록 확인"
docker exec "$WEB_CONTAINER" airflow dags list | sed -n '1,40p'

echo "✓ Airflow 동기화 완료"
echo "  web: $WEB_CONTAINER"
echo "  scheduler: $SCHEDULER_CONTAINER"
