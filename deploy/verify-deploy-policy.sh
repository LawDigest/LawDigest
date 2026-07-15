#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

for retired_path in \
  "$REPO_ROOT/deploy/deploy-airflow.sh" \
  "$REPO_ROOT/deploy/AIRFLOW_DEPLOY.md"; do
  if [ -e "$retired_path" ]; then
    echo "폐기된 Airflow 배포 진입점이 다시 추가되었습니다: $retired_path" >&2
    exit 1
  fi
done

while IFS= read -r deployment_file; do
  if grep -Ein \
    'infra/airflow|deploy-airflow|airflow-(webserver|scheduler|worker|triggerer)' \
    "$deployment_file"; then
    echo "운영 배포 경로에서 폐기된 Airflow 참조를 발견했습니다: $deployment_file" >&2
    exit 1
  fi
done < <(
  {
    find "$REPO_ROOT/deploy" -maxdepth 1 -type f -name '*.sh' \
      ! -name 'verify-deploy-policy.sh'
    find "$REPO_ROOT/.github/workflows" -maxdepth 1 -type f \
      \( -name '*.yml' -o -name '*.yaml' \)
  } | sort
)

echo "배포 정책 확인 완료: Airflow 배포 경로 없음"
