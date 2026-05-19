# Airflow Deprecated

Lawdigest 데이터 파이프라인의 표준 실행 경로는 더 이상 Airflow가 아닙니다.

현재 표준 실행 경로:

```bash
PYTHONPATH=services/data/src:services/ai/src python -m lawdigest_data.runtime.cli --help
```

Airflow 파일은 과거 DAG 파라미터와 실행 순서를 참고하기 위한 legacy artifact로만 유지합니다. 신규 파이프라인 기능은 `services/data/src/lawdigest_data/runtime/`에 추가합니다.
