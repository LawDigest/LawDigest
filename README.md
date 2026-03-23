# 모두의 입법 (LawDigest)

국회 법안 정보를 AI로 요약하여 누구나 쉽게 읽을 수 있도록 제공하는 서비스입니다.

---

## 서비스 구성

```
services/
├── web/      # Next.js 프론트엔드
├── backend/  # Spring Boot API 서버
├── data/     # 데이터 수집 파이프라인 (Python)
└── ai/       # AI 요약 및 RAG 챗봇 서비스 (Python)
```

### web — 프론트엔드

- **기술 스택**: Next.js 13, TypeScript, NextUI, Tailwind CSS
- 법안 피드 UI, 태그 필터링, 상세 페이지 제공
- 포트: `3000`

### backend — API 서버

- **기술 스택**: Spring Boot 3.1, Java, Spring Security
- 법안 조회 / 검색 / 유저 관리 REST API 제공
- MySQL + Redis 연동

### data — 데이터 수집 파이프라인

- **기술 스택**: Python 3.10+, pandas
- 국회 의안 Open API에서 법안 데이터를 수집하여 DB에 적재
- Airflow로 주기적 실행 (`lawdigest_bill_ingest_dag`, `lawdigest_hourly_update_dag` 등)
- 책임 범위: 수집 → 정제 → DB 적재 (AI 가공은 `services/ai` 담당)

### ai — AI 서비스

- **기술 스택**: Python 3.10+, pydantic-ai, OpenAI, Qdrant, LangChain
- 두 가지 책임을 가짐:

| 모듈 | 역할 |
|------|------|
| `processor/` | DB에 적재된 법안을 AI로 요약 (즉시 요약 / OpenAI Batch API) |
| `rag/` | Qdrant 벡터 DB + LLM 기반 RAG 챗봇 응답 |

---

## 인프라

```
infra/
├── airflow/   # 파이프라인 오케스트레이션
├── db/        # MySQL 스키마
└── prometheus/ # 모니터링
```

### 주요 Airflow DAG

| DAG | 주기 | 역할 |
|-----|------|------|
| `lawdigest_bill_ingest_dag` | 매시간 | 국회 API → DB 법안 수집 |
| `lawdigest_hourly_update_dag` | 매시간 | 법안 상태 업데이트 |
| `lawdigest_ai_summary_instant_dag` | 수동 | 단일 법안 즉시 AI 요약 |
| `lawdigest_ai_batch_submit_dag` | 수동 | OpenAI 배치 요약 제출 |
| `lawdigest_ai_batch_ingest_dag` | 수동 | 배치 요약 결과 수집 |
| `lawdigest_daily_db_backup_dag` | 매일 | DB 백업 |

---

## 로컬 실행

### 사전 요구사항

- Docker, Docker Compose
- Python 3.10+
- Java 17+
- Node.js 18+

### 인프라 실행

```bash
docker-compose up -d mysql redis
```

### 서비스별 실행

**백엔드**
```bash
cd services/backend
./gradlew bootRun
```

**프론트엔드**
```bash
cd services/web
npm install
npm run dev
```

**데이터 파이프라인**
```bash
cd services/data
pip install -e .
python -m lawdigest_data_pipeline.WorkFlowManager
```

**AI 서비스**
```bash
cd services/ai
pip install -e .
# 환경변수 설정 (.env)
cp .env.example .env
```

### 환경변수 (.env)

```env
# OpenAI
OPENAI_API_KEY=
SUMMARY_STRUCTURED_MODEL=openai:gpt-4o-mini
SUMMARY_STRUCTURED_FALLBACK_MODEL=openai:gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# Database
DB_HOST=
DB_PORT=3306
DB_USER=
DB_PASSWORD=
DB_NAME=

# Test Database
TEST_DB_HOST=
TEST_DB_PORT=3306
TEST_DB_USER=
TEST_DB_PASSWORD=
TEST_DB_NAME=

# Qdrant (RAG 챗봇 사용 시)
QDRANT_HOST=
QDRANT_API_KEY=
QDRANT_USE_HTTPS=false
```

---

## 아키텍처

```
국회 Open API
     ↓
services/data  ──→  MySQL RDS
                        ↑
services/ai    ──→  AI 요약 결과 업데이트
                        ↑
services/backend ──→  REST API
                        ↑
services/web   ──→  사용자 브라우저
```

---

## 테스트

```bash
# AI 서비스
cd services/ai
python3 -m pytest tests/ -v

# 백엔드
cd services/backend
./gradlew test
```
