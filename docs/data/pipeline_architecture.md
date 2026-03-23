# Lawdigest 데이터 파이프라인 아키텍처

> 작성일: 2026-03-23
> 현재 상태: **Airflow 실행 중, 모든 DAG 일시정지(paused) 상태**

---

## 1. 개요

Lawdigest 데이터 파이프라인은 국회 Open API에서 법안 데이터를 수집하고, AI 요약을 생성하여 MySQL RDS에 저장하는 자동화 시스템입니다. Apache Airflow 3.1 (CeleryExecutor)을 오케스트레이터로 사용하며, 수집→정제→저장→AI요약의 4단계로 구성됩니다.

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
        │                                       │
        ▼                                       │
  WorkFlowManager (오케스트레이션)               │
        │                                       ▼
        ▼                             AI Processor
  APISender ──→ Spring Boot API        ├── Batch Submit (OpenAI Batch API)
                                       ├── Batch Ingest (결과 수신)
                                       └── Instant Summarizer (즉시 요약)
                                               │
                                               ▼
                                         Qdrant (Vector DB / RAG)
```

---

## 3. 기술 스택

| 구성 요소 | 기술 | 버전 |
|---------|------|------|
| 오케스트레이터 | Apache Airflow (CeleryExecutor) | 3.1.8 |
| 메시지 브로커 | Redis | latest |
| Airflow 메타DB | PostgreSQL | 13 |
| 프로덕션 DB | MySQL | 8.0.35 |
| 데이터 처리 | Python + pandas | - |
| AI 요약 (Primary) | OpenAI GPT-5 / gpt-4o-mini | - |
| AI 요약 (Fallback) | Google Gemini 3-Flash | - |
| 구조화 AI | PydanticAI | - |
| 벡터 DB | Qdrant | - |
| 모니터링 | Prometheus + Grafana | - |
| 컨테이너 | Docker Compose | - |

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
| `ai_batch_jobs` | OpenAI 배치 작업 메타데이터 |
| `ai_batch_items` | 배치 항목별 AI 결과 |

---

## 5. Airflow DAG 목록

### 5.1 자동 스케줄 DAG

| DAG ID | 스케줄 | 용도 |
|--------|--------|------|
| `lawdigest_bill_ingest_dag` | `0 * * * *` (매 정시) | 국회 API → DB 수집 |
| `lawdigest_hourly_update_dag` | `0 * * * *` (매 정시) | 법안 상세 정보 동기화 |
| `lawdigest_ai_batch_submit_dag` | `10 * * * *` (매 정시 10분) | 미요약 법안 → OpenAI Batch 제출 |
| `lawdigest_ai_batch_ingest_dag` | `*/10 * * * *` (10분마다) | OpenAI 배치 결과 수신 → DB |
| `lawdigest_daily_db_backup_dag` | `0 0 * * *` (매일 자정) | 전체 DB 백업 |

### 5.2 수동 실행 DAG

| DAG ID | 용도 |
|--------|------|
| `lawdigest_ai_summary_batch_dag` | 결측된 AI 요약 일괄 복구 |
| `lawdigest_ai_summary_instant_dag` | 단일 법안 즉시 요약 |
| `manual_collect_bills` | 특정 기간 법안 수동 수집 |

---

## 6. DAG 상세 흐름

### 6.1 lawdigest_bill_ingest_dag (매 정시)

```
DataFetcher.fetch_bills_data()
    ↓
DataProcessor.process_congressman_bills()
    ↓ (중복 제거, 의원 ID 매핑)
DatabaseManager.upsert_bill() x 1000개 청크
```

**실행 모드**: `dry_run` | `test` | `prod`
**파라미터**: `start_date`, `end_date`, `age`(기본: 22대)

---

### 6.2 lawdigest_hourly_update_dag (매 정시)

```
update_lawmakers
    ↓
update_bills
    ↓ (병렬)
update_timeline ─┐
update_results  ─┤ 동시 실행
update_votes    ─┘
```

**태스크 함수**: `WorkFlowManager.update_*_data()`

---

### 6.3 AI 배치 파이프라인

```
[정시 10분] ai_batch_submit_dag
  DB에서 brief_summary/gpt_summary IS NULL 조회 (최대 200개)
      ↓
  JSONL 파일 생성 (gpt-4o-mini 요청 형식)
      ↓
  OpenAI API: 파일 업로드 → 배치 작업 생성
      ↓
  DB: ai_batch_jobs, ai_batch_items에 상태 저장

[10분마다] ai_batch_ingest_dag
  진행 중인 배치 상태 폴링
      ↓ (COMPLETED 시)
  결과 파일 다운로드 → JSONL 파싱
      ↓
  Bill 테이블: brief_summary, gpt_summary, summary_tags 업데이트
```

**비용**: Batch API는 일반 API 대비 50% 저렴 (결과: 최대 24시간 소요)

---

## 7. 핵심 모듈

### 7.1 DataFetcher

**경로**: `services/data/src/lawdigest_data_pipeline/DataFetcher.py` (1,345줄)

- 국회 Open API 및 공공데이터포털 연동
- HTTPAdapter + Retry 전략 (최대 3회, 0.5/1/2초 백오프)
- JSON/XML 파싱 → pandas DataFrame
- 28개 fetch 메서드 (법안, 의원, 표결, 타임라인 등)

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

**경로**: `services/data/src/lawdigest_data_pipeline/WorkFlowManager.py` (857줄)

**실행 모드**:
- `remote`: 운영 모드 (DB 직접 적재)
- `test`: 테스트 DB 사용
- `dry-run`: 수집만, 저장 없음
- `local`: 로컬 개발 모드

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
