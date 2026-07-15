# Airflow 폐기 상태

Lawdigest 데이터 파이프라인의 표준 실행 경로는 더 이상 Airflow가 아닙니다.

## 운영 정책

- Airflow는 빌드·배포·운영 대상이 아닙니다.
- `infra/airflow/` 아래 파일은 과거 DAG 파라미터와 실행 순서를 확인하기 위한
  legacy reference입니다.
- Docker Compose 구성과 DAG를 운영 서버에서 기동하지 않습니다.
- 과거 운영 배포 진입점인 `deploy/deploy-airflow.sh`와 배포 가이드는
  2026-07-15에 제거했습니다.
- 신규 파이프라인 기능과 운영 자동화는 자체 런타임에 추가합니다.

현재 표준 실행 경로:

```bash
PYTHONPATH=services/data/src:services/ai/src python -m lawdigest_data.runtime.cli --help
```

현재 런타임 구현은 `services/data/src/lawdigest_data/runtime/`에 있습니다.
