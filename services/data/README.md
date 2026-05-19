# Lawdigest Data Pipeline

모두의입법 프로젝트의 데이터 수집, 가공, 적재, 상태 동기화 런타임입니다.

## 운영 기준

현재 표준 오케스트레이터는 Airflow가 아니라 자체 `lawdigest-pipeline` CLI입니다.

- 표준 런타임: `src/lawdigest_data/runtime/`
- 표준 실행 로그: `/tmp/lawdigest-pipeline/pipeline-runs.jsonl`
- 표준 AI 요약: `ai-summary --cli-provider gemini`
- Gemini 장애 fallback: Codex CLI `gpt-5.3-codex-spark`
- Airflow/n8n: legacy reference

상세 문서:

- [데이터 파이프라인 아키텍처](../../docs/data/법안%20데이터%20파이프라인/pipeline_architecture.md)
- [데이터 파이프라인 런타임 런북](../../docs/data/법안%20데이터%20파이프라인/pipeline_restart_runbook.md)

## 빠른 실행

프로젝트 루트에서 실행합니다.

```bash
cd /home/ubuntu/project/Lawdigest
PYTHONPATH=services/data/src:services/ai/src python -m lawdigest_data.runtime.cli --help
```

패키지 설치 환경에서는 console script도 사용할 수 있습니다.

```bash
lawdigest-pipeline --help
```

## 주요 명령

| 명령 | 역할 |
|------|------|
| `bill-ingest` | 국회 Open API 법안 수집, 정제, DB 반영 |
| `bill-status-sync` | 의원, lifecycle, vote 상태 동기화 |
| `ai-summary` | Gemini CLI 기반 실시간 AI 요약 |
| `ai-repair-cli` | CLI 기반 결측 요약 복구 alias |
| `ai-repair-native` | OpenAI/Gemini API 기반 결측 요약 복구 |
| `ai-batch-submit` | legacy Batch API 제출 |
| `ai-batch-ingest` | legacy Batch API 결과 회수 |

## 표준 AI 요약 예시

```bash
PYTHONPATH=services/data/src:services/ai/src python -m lawdigest_data.runtime.cli \
  ai-summary \
  --mode dry_run \
  --read-mode prod \
  --target-mode latest \
  --cli-provider gemini \
  --limit 5 \
  --batch-size 1 \
  --output-path /tmp/lawdigest-gemini-cli-summary.json
```

`dry_run`은 DB를 갱신하지 않고 결과 JSON만 저장합니다.

## Airflow 상태

Airflow는 신규 운영 경로에서 제외되었습니다.

- `infra/airflow/dags/*`: legacy reference
- `infra/airflow/docker-compose.yaml`: legacy reference
- 신규 기능 추가 위치: `src/lawdigest_data/runtime/`

과거 Airflow 문서는 `docs/data/legacy/`에 보관합니다.
