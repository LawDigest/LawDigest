# Airflow Deploy Guide

이 문서는 `airflow.lawdigest.cloud`에 연결된 운영 Airflow를 코드 변경 후 다시 동기화하는 절차를 설명한다.

Airflow는 기본적으로 `/home/ubuntu/project/Lawdigest`를 볼륨 마운트해서 읽는다.
운영 루트에 다른 작업이 있으면 `LAWDIGEST_PROJECT_DIR`로 깨끗한 전용 worktree를
지정할 수 있다. GitHub merge만으로는 반영되지 않으므로 실제 마운트 경로도 같은
커밋으로 전환해야 한다.

## 목적
- 운영 Airflow가 보는 DAG 파일을 최신 상태로 갱신
- `git pull` 후 `airflow-webserver`, `airflow-scheduler`를 재기동
- DAG import 오류를 즉시 확인

## 구성
- 동기화 스크립트: [deploy-airflow.sh](/home/ubuntu/project/Lawdigest/.worktrees/airflow-workflow-manager/deploy/deploy-airflow.sh)
- 실제 체크아웃 경로: `/home/ubuntu/project/Lawdigest`
- Airflow Compose 파일: `infra/airflow/docker-compose.yaml`

## 동작 방식
스크립트는 아래 순서로 동작한다.

1. 대상 worktree 또는 repo root를 확인한다.
2. `git pull --ff-only`로 최신 커밋을 가져온다.
3. `airflow-webserver`, `airflow-scheduler`를 재기동한다.
4. `airflow dags list-import-errors`로 파싱 오류를 확인한다.
5. `airflow dags list`로 DAG 목록이 최신인지 확인한다.

## 기본 사용법

```bash
./deploy/deploy-airflow.sh
```

특정 worktree를 지정하려면:

```bash
./deploy/deploy-airflow.sh /path/to/worktree
```

유지보수 창에서 이미 검증한 정확한 커밋의 전용 worktree를 사용하고, 중단된 전체
Celery 구성을 복구해야 하는 경우 다음처럼 실행한다.

```bash
AIRFLOW_SKIP_GIT_PULL=true \
AIRFLOW_FULL_STACK=true \
AIRFLOW_BUILD_IMAGE=true \
./deploy/deploy-airflow.sh /path/to/exact-commit-worktree
```

- `AIRFLOW_SKIP_GIT_PULL=true`: detached worktree의 정확한 커밋을 유지한다.
- `AIRFLOW_FULL_STACK=true`: webserver, scheduler, worker, triggerer, log-pruner와
  의존 서비스를 함께 기동한다.
- `AIRFLOW_BUILD_IMAGE=true`: 로컬 Airflow 이미지가 없거나 의존성이 변경됐을 때
  이미지를 다시 빌드한다.
- Compose 환경 파일은 공유 저장소의 `infra/airflow/.env`, data 환경 파일은
  공유 저장소의 `services/data/.env`를 기본으로 사용한다.

## 배포 확인

```bash
docker exec airflow-airflow-webserver-1 airflow dags list
docker exec airflow-airflow-webserver-1 airflow dags list-import-errors
```

## 주의사항
- 이 스크립트는 운영 Airflow가 실제로 바라보는 checkout에서 실행해야 한다.
- worktree 경로를 인자로 넣으면 기본적으로 그 경로를 pull한다. 정확한 detached
  커밋을 배포할 때만 `AIRFLOW_SKIP_GIT_PULL=true`를 사용한다.
- `.runtime/` 같은 테스트 배포 구조와는 별개다.
