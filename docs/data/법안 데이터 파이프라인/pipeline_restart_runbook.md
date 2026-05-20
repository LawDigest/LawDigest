# 데이터 파이프라인 런타임 런북

> 작성일: 2026-05-19
> 현재 방향: **Airflow 폐기, 자체 `lawdigest-pipeline` 런타임으로 전환**

---

## 1. 운영 원칙

Lawdigest 데이터 파이프라인은 더 이상 Airflow DAG를 표준 실행 경로로 보지 않습니다.

기존 Airflow DAG는 구현 참고용 legacy artifact로만 남기고, 실제 실행은 `lawdigest_data.runtime`의 `lawdigest-pipeline` CLI를 기준으로 합니다. AI 요약 표준 경로는 배치 제출/회수가 아니라 Codex CLI `gpt-5.3-codex-spark` 기반 실시간 처리입니다. 실행 결과는 append-only JSONL 로그로 남기며, 이후 직접 구현할 파이프라인 모니터링 사이트는 이 실행 이력을 읽는 구조로 확장합니다.

기본 실행 로그:

```bash
/tmp/lawdigest-pipeline/pipeline-runs.jsonl
```

운영 로그 위치를 고정하려면:

```bash
export LAWDIGEST_PIPELINE_LOG_DIR=/var/log/lawdigest-pipeline
```

---

## 2. 실행 환경

로컬/서버 체크아웃에서 아래처럼 실행합니다.

```bash
cd /home/ubuntu/project/Lawdigest
PYTHONPATH=services/data/src:services/ai/src python -m lawdigest_data.runtime.cli --help
```

패키지 설치 환경에서는 console script도 사용할 수 있습니다.

```bash
lawdigest-pipeline --help
```

---

## 3. 핵심 명령

### 3.1 법안 수집

```bash
PYTHONPATH=services/data/src:services/ai/src python -m lawdigest_data.runtime.cli \
  bill-ingest \
  --mode dry_run \
  --start-date 2026-05-19 \
  --end-date 2026-05-19 \
  --age 22
```

운영 반영:

```bash
PYTHONPATH=services/data/src:services/ai/src python -m lawdigest_data.runtime.cli \
  bill-ingest \
  --mode prod \
  --start-date 2026-05-19 \
  --end-date 2026-05-19 \
  --age 22
```

### 3.2 법안 상태 동기화

```bash
PYTHONPATH=services/data/src:services/ai/src python -m lawdigest_data.runtime.cli \
  bill-status-sync \
  --mode dry_run \
  --start-date 2026-05-19 \
  --end-date 2026-05-19 \
  --age 22
```

### 3.3 AI 실시간 요약 (표준)

```bash
PYTHONPATH=services/data/src:services/ai/src python -m lawdigest_data.runtime.cli \
  ai-summary \
  --mode dry_run \
  --cli-provider codex \
  --limit 1 \
  --batch-size 1 \
  --output-path /tmp/lawdigest-codex-cli-summary.json
```

이 경로는 Codex CLI headless 실행 결과를 기존 API 배치와 같은 `BatchStructuredSummary` 스키마로 검증합니다. 응답 키는 `briefSummary`, `gptSummary`, `tags`만 허용하고, DB에는 기존 컬럼인 `brief_summary`, `gpt_summary`, `summary_tags`로 반영합니다.

Codex smoke 예시:

```bash
PYTHONPATH=services/data/src:services/ai/src python -m lawdigest_data.runtime.cli \
  ai-summary \
  --mode dry_run \
  --read-mode prod \
  --target-mode latest \
  --cli-provider codex \
  --limit 1 \
  --batch-size 1 \
  --output-path /tmp/lawdigest-codex-smoke.json
```

이 smoke는 최신 법안 1건을 Codex CLI로 요약해 구조화 응답 계약을 확인합니다. `dry_run`이므로 DB에는 반영하지 않습니다.

### 3.4 AI Batch 제출 (legacy fallback)

```bash
PYTHONPATH=services/data/src:services/ai/src python -m lawdigest_data.runtime.cli \
  ai-batch-submit \
  --mode dry_run \
  --provider gemini \
  --limit 5
```

### 3.5 AI Batch 결과 회수 (legacy fallback)

```bash
PYTHONPATH=services/data/src:services/ai/src python -m lawdigest_data.runtime.cli \
  ai-batch-ingest \
  --mode dry_run \
  --provider all \
  --max-jobs 5
```

### 3.6 Native API 기반 결측 요약 복구

```bash
PYTHONPATH=services/data/src:services/ai/src python -m lawdigest_data.runtime.cli \
  ai-repair-native \
  --mode dry_run \
  --provider gemini \
  --limit 5 \
  --batch-size 1 \
  --output-path /tmp/lawdigest-native-repair.json
```

### 3.7 CLI 기반 결측 요약 복구 (compatibility alias)

```bash
PYTHONPATH=services/data/src:services/ai/src python -m lawdigest_data.runtime.cli \
  ai-repair-cli \
  --mode dry_run \
  --cli-provider codex \
  --limit 1 \
  --batch-size 1 \
  --output-path /tmp/lawdigest-cli-repair.json
```

`ai-repair-cli`는 기존 명령 호환용입니다. 신규 운영에서는 `ai-summary --cli-provider codex`를 우선 사용합니다.

사용 가능한 CLI provider:

- `codex`
- `gemini`
- `claude`

---

## 4. 스케줄 운영

Airflow 대신 `systemd timer` 또는 cron을 사용합니다. 우선은 수동 실행으로 검증하고, 스케줄이 필요해지면 아래 순서로 timer를 추가합니다.

1. `/usr/local/bin/lawdigest-pipeline-wrapper`에 `PYTHONPATH`와 작업 디렉터리를 고정
2. `bill-ingest`, `bill-status-sync`, `ai-summary`를 각각 별도 timer로 등록
3. timer stdout/stderr는 journald와 `pipeline-runs.jsonl` 양쪽에서 확인
4. 실패 알림은 모니터링 사이트 또는 별도 notifier에서 후속 구현

---

## 5. Airflow 폐기 상태

Airflow는 신규 운영 경로에서 제외합니다.

- `infra/airflow/dags/*`: legacy reference
- `infra/airflow/docker-compose.yaml`: legacy reference
- Airflow 컨테이너 재기동/재배포: 중단
- 신규 파이프라인 기능: `lawdigest_data.runtime`에만 추가

Airflow 파일을 완전히 삭제하기 전까지는 과거 DAG의 파라미터와 실행 순서를 참고할 수 있지만, 운영 판단은 `lawdigest-pipeline` 결과와 JSONL 실행 로그를 기준으로 합니다.

---

## 6. 다음 모니터링 사이트 설계 기준

직접 구현할 데이터 파이프라인 모니터링 사이트는 우선 아래 데이터를 읽으면 됩니다.

- 최근 run 목록
- command별 성공/실패 횟수
- step별 처리 결과
- 실패 traceback
- 산출물 JSON 경로
- provider별 AI 요약 성공률

초기 데이터 소스는 `pipeline-runs.jsonl`이고, 운영 필요성이 커지면 같은 이벤트를 DB 테이블(`pipeline_runs`, `pipeline_run_steps`, `pipeline_artifacts`)에도 기록합니다.
