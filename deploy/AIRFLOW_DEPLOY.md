# Airflow Deploy Guide

이 문서는 `airflow.lawdigest.cloud`에 연결된 운영 Airflow를 코드 변경 후 다시 동기화하는 절차를 설명한다.

현재 Airflow는 `/home/ubuntu/project/Lawdigest`를 볼륨 마운트해서 읽는다.  
따라서 GitHub merge만으로는 반영되지 않고, 실제 호스트 체크아웃이 최신 커밋을 받아야 한다.

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

## 배포 확인

```bash
docker exec airflow-airflow-webserver-1 airflow dags list
docker exec airflow-airflow-webserver-1 airflow dags list-import-errors
```

## 주의사항
- 이 스크립트는 운영 Airflow가 실제로 바라보는 checkout에서 실행해야 한다.
- worktree 경로를 인자로 넣으면 그 경로를 pull한다. 운영 반영이 목적이면 `/home/ubuntu/project/Lawdigest`를 사용한다.
- `.runtime/` 같은 테스트 배포 구조와는 별개다.
