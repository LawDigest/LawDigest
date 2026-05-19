# Lawdigest 데이터 파이프라인 아키텍처

> 작성일: 2026-03-23
> 갱신일: 2026-05-19
> 현재 상태: **Airflow 폐기, 자체 `lawdigest-pipeline` 런타임으로 전환**

---

## 1. 개요

Lawdigest 데이터 파이프라인은 국회 Open API에서 법안 데이터를 수집하고, AI 요약을 생성하여 MySQL RDS에 저장하는 자동화 시스템입니다. 기존 Airflow DAG는 legacy reference로 남기되, 표준 실행 경로는 자체 `lawdigest-pipeline` CLI 런타임입니다. 수집→정제→저장→Gemini CLI 실시간 요약의 4단계는 기존 Python 모듈을 재사용하고, 실행 이력은 JSONL 이벤트 로그로 남깁니다.

---

## 2. 전체 아키텍처

```
국회 Open API (openapi.assembly.go.kr)
        │
        ▼
  DataFetcher (수집)
        │
        ▼
  DataProcessor (정제/변환)
        │
        ▼
  DatabaseManager (저장) ──────────────→ MySQL RDS (lawDB / lawTestDB)
        │
        ├── PipelineRuntime / lawdigest-pipeline
        │       ├── bill-ingest
        │       ├── bill-status-sync
        │       ├── ai-summary
        │       ├── ai-batch-submit
        │       ├── ai-batch-ingest
        │       ├── ai-repair-native
        │       └── ai-repair-cli
        │
        ▼
  AI Processor
        ├── Gemini CLI Realtime Summary (표준)
        ├── Pydantic Schema Validation (briefSummary / gptSummary / tags)
        ├── Instant Summarizer (provider-aware API fallback)
        └── Batch Submit/Ingest (legacy fallback)
                │
                ▼
          Qdrant (Vector DB / RAG)

  pipeline-runs.jsonl (실행 이력 / 모니터링 사이트 입력)
```

---

## 3. 기술 스택

| 구성 요소 | 기술 | 버전 |
|---------|------|------|
| 파이프라인 런타임 | `lawdigest-pipeline` CLI | - |
| 실행 이력 | JSONL (`pipeline-runs.jsonl`) | - |
| 프로덕션 DB | MySQL | 8.0.35 |
| 데이터 처리 | Python + pandas | - |
| AI 요약 (표준) | Google Gemini CLI 실시간 실행 | - |
| API/Batch Fallback | OpenAI + Gemini | - |
| CLI 보조 경로 | Codex CLI / Claude CLI | - |
| 구조화 AI | Pydantic/PydanticAI 스키마 계약 | - |
| 벡터 DB | Qdrant | - |
| 모니터링 | 자체 파이프라인 모니터링 사이트 (예정) | - |

---

## 4. 데이터베이스 구성

### 4.1 프로덕션 DB
- **Host**: 140.245.74.246:2835
- **Database**: `lawDB`
- **User**: root

### 4.2 테스트 DB
- **Host**: 140.245.74.246:2812
- **Database**: `lawTestDB`
- **User**: root

### 4.3 주요 테이블

| 테이블 | 용도 |
|--------|------|
| `bill` | 법안 기본 정보 (bill_id PK) |
| `lawmaker` | 국회의원 정보 |
| `bill_timeline` | 법안 처리 타임라인 |
| `bill_result` | 법안 처리 결과 |
| `bill_vote` | 의원별 표결 정보 |
| `ai_batch_jobs` | provider별 배치 작업 메타데이터 |
| `ai_batch_items` | 배치 항목별 AI 결과 |

---

## 5. 자체 런타임 명령 목록

| 명령 | 용도 |
|------|------|
| `bill-ingest` | 국회 API → artifact → DB 수집 |
| `bill-status-sync` | 법안 lifecycle/vote 상태 동기화 |
| `ai-summary` | Gemini CLI 기반 실시간 결측 요약 생성 |
| `ai-batch-submit` | legacy: 미요약 법안 → 선택한 provider의 Batch 제출 |
| `ai-batch-ingest` | legacy: provider별 배치 결과 수신 → DB |
| `ai-repair-native` | fallback: OpenAI/Gemini API 기반 결측 요약 복구 |
| `ai-repair-cli` | compatibility alias: Gemini/Codex/Claude CLI 기반 결측 요약 복구 |

기본 실행 형태:

```bash
PYTHONPATH=services/data/src:services/ai/src python -m lawdigest_data.runtime.cli <command> [options]
```

실행 이력:

```bash
/tmp/lawdigest-pipeline/pipeline-runs.jsonl
```

---

## 6. 자체 런타임 상세 흐름

### 6.1 bill-ingest

```
fetch_bills_from_api
    ↓
process_bills
    ↓
upsert_bills
```

**WorkFlowManager 내부 단계**:
- `fetch_bills_data_step()` : 원천 법안 수집 후 아티팩트 저장
- `process_bills_data_step()` : 의원 발의자 가공 및 DB 적재용 row 생성
- `upsert_bills_data_step()` : 최종 DB 반영

**실행 모드**: `dry_run` | `test` | `prod`
**파라미터**: `start_date`, `end_date`, `age`(기본: 22대)

---

### 6.2 bill-status-sync

```
update_lawmakers
    ↓
fetch_lifecycle
    ↓
upsert_lifecycle

update_lawmakers
    ↓
fetch_vote
    ↓
upsert_vote
```

**태스크 함수**: `WorkFlowManager.update_lawmakers_data()`, `fetch_lifecycle_step()`, `upsert_lifecycle_step()`, `fetch_vote_step()`, `upsert_vote_step()`

**설계 원칙**:
- 상태 동기화는 `timeline / result / vote` 테이블 기준이 아니라 `lifecycle + vote` capability 기준으로 운영
- `lifecycle`은 `ALLBILL` snapshot 기반으로 `BillTimeline`과 `Bill` 최신 상태 projection을 함께 갱신
- `vote`는 `VoteRecord`, `VoteParty`를 함께 반영
- 각 capability는 artifact와 source별 checkpoint를 별도로 가짐

---

### 6.3 AI 요약 표준 경로: Gemini CLI 실시간 처리

```
ai-summary
  DB에서 summary는 있으나 brief_summary/gpt_summary가 없는 법안 조회
      ↓
  Gemini CLI headless 실행
      ↓
  기존 API 배치와 동일한 프롬프트 적용
      ↓
  BatchStructuredSummary Pydantic 스키마 검증
      ↓
  Bill 테이블: brief_summary, gpt_summary, summary_tags 업데이트
```

**운영 포인트**:
- 표준 요약 명령은 `ai-summary --cli-provider gemini`
- 응답 키는 기존 API 배치와 같은 `briefSummary`, `gptSummary`, `tags`
- 파싱 후 DB 컬럼에는 기존 컬럼명인 `brief_summary`, `gpt_summary`, `summary_tags`로 저장
- `tags`는 Pydantic 스키마로 정확히 5개를 검증

### 6.4 AI 배치 파이프라인 (legacy fallback)

```
ai-batch-submit
  DB에서 brief_summary/gpt_summary IS NULL 조회
      ↓
  provider별 요청 파일 생성 (OpenAI JSONL / Gemini Batch File API)
      ↓
  선택한 provider API: 파일 업로드 → 배치 작업 생성
      ↓
  DB: ai_batch_jobs, ai_batch_items에 상태 저장

ai-batch-ingest
  provider=all 기준 진행 중 배치 상태 폴링
      ↓ (COMPLETED 시)
  결과 파일 다운로드 → JSONL 파싱
      ↓
  Bill 테이블 업데이트
```

**운영 포인트**:
- 배치 submit/ingest는 신규 표준 경로가 아니라 legacy fallback
- 대량 백필 비용/시간을 따로 통제해야 할 때만 사용
- `ai_batch_jobs`는 `(provider, batch_id)` 복합 유니크 기준으로 관리

### 6.5 수동 AI 요약 경로

```
ai-repair-native / instant helper
  bill_json 또는 개별 bill 필드 입력
      ↓
  provider=openai|gemini 선택
      ↓
  즉시 structured summary 생성
      ↓
  선택적으로 Bill 테이블 즉시 반영

ai-repair-native
  DB에서 summary는 있으나 AI 요약이 없는 법안 조회
      ↓
  provider=openai|gemini 선택
      ↓
  배치 단위로 요약 생성
      ↓
  dry_run 또는 test/prod DB 반영 + JSON 리포트 저장
```

**운영 포인트**:
- native API 요약 경로는 `provider`, `model` 파라미터를 지원
- Gemini instant/repair API 경로는 fallback으로 유지
- `ai-repair-cli`는 기존 compatibility alias이며, 신규 운영 문서에서는 `ai-summary`를 우선 사용
- Codex/Claude CLI provider는 Gemini CLI 장애 시 보조 비교 경로로만 사용

---

## 7. 핵심 모듈

### 7.1 DataFetcher

**경로**: `services/data/src/lawdigest_data/bills/DataFetcher.py`

- 국회 Open API 및 공공데이터포털 연동
- HTTPAdapter + Retry 전략 (최대 3회, 0.5/1/2초 백오프)
- JSON/XML 파싱 → pandas DataFrame
- 법안 본체 적재, 의원, 표결 등 기존 수집 경로 제공
- 상태 동기화는 직접 `DataFetcher` 메서드를 호출하기보다 capability fetcher (`status/lifecycle_fetcher.py`, `status/vote_fetcher.py`)를 통해 사용

**API 키 환경변수**:
- `APIKEY_billsContent`, `APIKEY_billsInfo`, `APIKEY_status`
- `APIKEY_result`, `APIKEY_lawmakers`, `APIKEY_DATAGOKR`

---

### 7.2 DataProcessor

**경로**: `services/data/src/lawdigest_data_pipeline/DataProcessor.py` (197줄)

- 법안명에서 발의자 추출 (정규표현식)
- 공동발의자 ID 매핑
- 발의자 종류 정규화: `의원` → `CONGRESSMAN`, `위원장` → `CHAIRMAN`, `정부` → `GOVERNMENT`

---

### 7.3 DatabaseManager

**경로**: `services/data/src/lawdigest_data_pipeline/DatabaseManager.py` (893줄)

- MySQL 8.0 연결 관리 (UTF8MB4, autocommit=False)
- Context Manager 기반 트랜잭션 (자동 commit/rollback)
- 청크 처리: CHUNK_SIZE = 1000
- DictCursor (딕셔너리 형태 결과 반환)

---

### 7.4 WorkFlowManager

**경로**: `services/data/src/lawdigest_data/core/WorkFlowManager.py`

**책임**:
- Airflow DAG가 호출하는 법안 파이프라인 오케스트레이션 담당
- `DataFetcher` / `DataProcessor` / `DatabaseManager`를 조합해 수집, 가공, 저장 흐름을 실행
- 본체 적재는 `fetch_bills_data_step -> process_bills_data_step -> upsert_bills_data_step` 구조를 사용
- 상태 동기화는 `BillStatusSyncService`를 통해 `lifecycle + vote` capability 기준으로 실행
- 실행 모드: `dry_run`, `test_db`/`test`, `prod`

### 7.5 BillStatusSyncService

**경로**: `services/data/src/lawdigest_data/core/bill_status_sync.py`

**책임**:
- `fetch_lifecycle_step`, `upsert_lifecycle_step`, `fetch_vote_step`, `upsert_vote_step` 제공
- artifact 저장과 checkpoint 갱신 규칙 관리
- `status/lifecycle_fetcher.py`, `status/vote_fetcher.py`, `status/projectors.py`를 조합해 상태 동기화 capability를 실행

---

## 8. 컨테이너 서비스 현황

| 컨테이너 | 포트 | 상태 | 역할 |
|---------|------|------|------|
| `airflow-airflow-webserver-1` | 8081 | unhealthy (기능 정상) | Airflow UI & API |
| `airflow-airflow-scheduler-1` | - | healthy | DAG 스케줄링 |
| `airflow-airflow-worker-1` | - | healthy | Celery 워커 |
| `airflow-airflow-triggerer-1` | - | healthy | 비동기 이벤트 |
| `airflow-airflow-log-pruner-1` | - | running | 로그 정리 (1GB) |
| `airflow-redis-1` | 6379 | healthy | Celery 브로커 |
| `airflow-postgres-1` | 5432 | healthy | Airflow 메타DB |
| `lawdigest-mysql` | 3306 | running | 프로덕션 DB |
| `lawdigest-redis` | 6379 | running | 앱 캐시 |

> **참고**: `airflow-webserver`의 `unhealthy` 상태는 헬스체크 경로 문제(`/health` → 404)이며, 실제 서비스(포트 8081)는 정상 응답 중.

---

## 9. 설정 파일 위치

| 파일 | 경로 | 용도 |
|------|------|------|
| `docker-compose.yml` | `Lawdigest/` | 프로덕션 서비스 (MySQL, Redis, Prometheus, Grafana) |
| `docker-compose.yaml` | `infra/airflow/` | Airflow 및 보조 서비스 |
| `.env` | `services/data/` | 데이터 파이프라인 환경변수 |
| `.env` | `infra/airflow/` | Airflow 설정 |
| `prometheus.yml` | `infra/prometheus/` | Prometheus 타겟 설정 |
| DAG 파일들 | `infra/airflow/dags/` | 8개 DAG 정의 |

---

## 10. 모니터링

- **Airflow UI**: http://localhost:8081 (계정: airflow / oracleserver2220!)
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000
- **Discord 알림**: 파이프라인 오류 시 자동 Discord Webhook 발송

---

## 11. 데이터 경로 (컨테이너 내부)

```
PYTHONPATH: /opt/airflow/project:/opt/airflow/project/services/data
프로젝트 루트: /opt/airflow/project  (← /home/ubuntu/project/Lawdigest 마운트)
DAG 디렉토리: /opt/airflow/dags
로그 디렉토리: /opt/airflow/logs
DB 백업: /opt/airflow/project/dump/
```
