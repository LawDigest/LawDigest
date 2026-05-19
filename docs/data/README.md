# Data Documentation Index

현재 데이터 파이프라인 문서는 운영 기준 문서와 legacy 기록을 분리합니다.

## 현재 운영 문서

| 문서 | 역할 |
|------|------|
| [법안 데이터 파이프라인 아키텍처](./법안%20데이터%20파이프라인/pipeline_architecture.md) | 자체 `lawdigest-pipeline` 런타임 기준 전체 구조 |
| [법안 데이터 파이프라인 런북](./법안%20데이터%20파이프라인/pipeline_restart_runbook.md) | 표준 실행 명령, smoke, 스케줄 운영 기준 |
| [상태 동기화 모니터링 쿼리](./법안%20데이터%20파이프라인/status_sync_monitoring_queries.md) | lifecycle/vote 동기화 검증 쿼리 |
| [Gemini CLI 최신 5건 요약 결과](./법안%20데이터%20파이프라인/reports/2026-05-19-gemini-cli-latest-5-summary.md) | 실시간 요약 샘플 리포트 |

## 보조 데이터 도메인

| 문서 | 역할 |
|------|------|
| [선거 데이터 파이프라인 계획](./선거%20데이터%20파이프라인/election-data-pipeline-plan.md) | 선거 데이터 수집 설계 |
| [여론조사 파서 개발 가이드](./여론조사%20파서%20개발/parser_development_guide.md) | 여론조사 PDF/표 파서 개발 기준 |

## Legacy 기록

`legacy/` 아래 문서는 Airflow, n8n, 과거 리팩터링 기록입니다. 새 운영 판단이나 신규 기능 추가 기준으로 사용하지 않습니다.

- Airflow 관련 파일은 `infra/airflow/DEPRECATED.md`와 함께 legacy reference로만 취급합니다.
- 신규 법안 파이프라인 기능은 `services/data/src/lawdigest_data/runtime/`에 추가합니다.
- 신규 AI 요약 표준 경로는 `ai-summary --cli-provider gemini`입니다.
