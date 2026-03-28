# lawdigest_codeserver

모두의입법 프로젝트의 데이터 수집, 가공, 적재 파이프라인 저장소입니다.

## 오케스트레이션 기준
- 운영 기준(2026-03-08 이후): **Airflow 단일 운영**
- `airflow/dags/`의 DAG를 기준으로 스케줄링합니다.
- `n8n/` 및 `scripts/run_n8n_*` 자산은 레거시 참조용이며, Airflow와 병행 스케줄링하지 않습니다.

## Airflow 빠른 실행
```bash
./scripts/airflow_control.sh up
./scripts/airflow_control.sh list-dags
./scripts/airflow_control.sh unpause-main
```

Airflow 웹 UI는 `http://localhost:8081`에서 확인할 수 있습니다.

## 주요 DAG
- `bill_ingest_dag`: 국회 API 기반 법안 수집 및 DB upsert
- `bill_status_sync_dag`: 의원/타임라인/결과/표결 상태 동기화
- `manual_bill_collect_dag`: 기간 파라미터 기반 수동 법안 수집
- `ai_batch_submit_dag`: 미요약 법안 배치 제출
- `ai_batch_ingest_dag`: AI 배치 결과 반영
- `db_backup_dag`: 일일 DB 백업

## 복귀 가이드
- 상세 롤백 절차: `docs/airflow_rollback_runbook.md`
- n8n 관련 문서는 레거시 기록으로 `docs/n8n_pipeline_migration.md`, `docs/n8n_import_guide.md`에 보관
