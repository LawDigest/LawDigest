<div align="center">

# 모두의입법

**복잡한 국회 법안, AI가 쉽게 읽어드립니다**

[![Next.js](https://img.shields.io/badge/Next.js-13-black?style=flat-square&logo=next.js)](https://nextjs.org/)
[![Spring Boot](https://img.shields.io/badge/Spring_Boot-3.1-6DB33F?style=flat-square&logo=springboot&logoColor=white)](https://spring.io/projects/spring-boot)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Gemini CLI](https://img.shields.io/badge/Gemini_CLI-Realtime_AI-4285F4?style=flat-square&logo=googlegemini&logoColor=white)](https://ai.google.dev/gemini-api/docs/cli)
[![Codex CLI](https://img.shields.io/badge/Codex_CLI-Fallback-412991?style=flat-square&logo=openai&logoColor=white)](https://developers.openai.com/codex)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=flat-square&logo=mysql&logoColor=white)](https://www.mysql.com/)

</div>

---

## 소개

**모두의 입법**은 국회에서 매일 쏟아지는 수백 건의 법률개정안을 AI가 핵심만 골라 요약해주는 서비스입니다.

어려운 법률 용어와 긴 원문 없이, 피드 형식의 친숙한 UI로 법안이 내 삶에 어떤 영향을 미치는지 한눈에 확인할 수 있습니다.

<br>

## 주요 기능

| 기능 | 설명 |
|------|------|
| **AI 법안 요약** | Gemini CLI 기반 실시간 요약 + Codex CLI fallback으로 법안 핵심 내용을 한 문장 + 항목별 상세 요약 제공 |
| **태그 분류** | 법안별 주제 태그 자동 생성으로 관심 분야 빠른 탐색 |
| **의원 / 정당 팔로우** | 관심 의원·정당의 법안 활동을 실시간으로 구독 |
| **법안 타임라인** | 발의 → 위원회 → 본회의까지 처리 단계 시각화 |
| **좋아요 & 알림** | 관심 법안 저장 및 상태 변경 알림 |
| **RAG 챗봇** | 법안 내용 기반 벡터 검색 + LLM 질의응답 |

<br>

## 기술 스택

### Frontend
![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)

### Backend
![Spring Boot](https://img.shields.io/badge/Spring_Boot-6DB33F?style=for-the-badge&logo=springboot&logoColor=white)
![Java](https://img.shields.io/badge/Java_17-ED8B00?style=for-the-badge&logo=openjdk&logoColor=white)
![Spring Security](https://img.shields.io/badge/Spring_Security-6DB33F?style=for-the-badge&logo=springsecurity&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-FF4438?style=for-the-badge&logo=redis&logoColor=white)

### AI / Data
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Gemini CLI](https://img.shields.io/badge/Gemini_CLI-4285F4?style=for-the-badge&logo=googlegemini&logoColor=white)
![Codex CLI](https://img.shields.io/badge/Codex_CLI-412991?style=for-the-badge&logo=openai&logoColor=white)
![Qdrant](https://img.shields.io/badge/Qdrant-FF4785?style=for-the-badge)

### Infrastructure
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white)

<br>

## 아키텍처

```mermaid
graph LR
    subgraph CLIENT["Client"]
        Browser["🌐 Browser"]
    end

    subgraph FRONTEND["services/web"]
        Web["Next.js 13"]
    end

    subgraph BACKEND["services/backend"]
        API["Spring Boot 3.1 | 법안 · 의원 · 유저 API"]
    end

    subgraph AI_SERVICE["services/ai"]
        Processor["processor | Gemini CLI 실시간 요약"]
        RAG["rag | RAG 챗봇"]
    end

    subgraph PIPELINE["services/data"]
        Runtime["lawdigest-pipeline | 자체 런타임"]
        Data["데이터 수집 | DataFetcher · DataProcessor"]
        RunLog[("pipeline-runs.jsonl")]
    end

    subgraph STORAGE["Storage"]
        DB[("MySQL RDS")]
        Redis[("Redis")]
        Qdrant[("Qdrant\n벡터 DB")]
    end

    subgraph EXTERNAL["External"]
        OpenAPI["🏛️ 국회 Open API"]
        Gemini["🤖 Gemini CLI"]
        Codex["🧠 Codex CLI fallback"]
        OpenAI["🤖 OpenAI / Gemini Batch legacy"]
    end

    %% --- 보이지 않는 연결로 수직 순서 고정 ---
    Processor ~~~ Data
    OpenAI ~~~ DB

    %% --- 실제 관계 정의 ---
    Browser --> Web
    Web -->|"REST"| API
    API --> DB
    API --> Redis

    Runtime -->|"bill-ingest"| Data
    Runtime -->|"ai-summary"| Processor
    Runtime -->|"실행 이력"| RunLog

    OpenAPI -->|"법안 데이터"| Data

    Processor -->|"실시간 요약"| Gemini
    Gemini -. "quota/API/CLI 실패" .-> Codex
    Processor -. "legacy batch fallback" .-> OpenAI
    RAG -->|"임베딩 / 생성"| OpenAI

    Processor -->|"요약 결과"| DB
    RAG <-->|"벡터 검색"| Qdrant
    Data -->|"적재"| DB
```

<br>

## 서비스 구성

### `services/web` — 프론트엔드
피드 기반 법안 브라우저. 법안 상세, 의원·정당 프로필, 검색, 팔로우, 마이페이지 등을 제공합니다.

### `services/backend` — API 서버
법안·의원·정당·유저 도메인의 REST API를 제공합니다. OAuth2 소셜 로그인, JWT 인증, Redis 캐싱을 포함합니다.

### `services/data` — 데이터 파이프라인
국회 의안 Open API에서 법안 데이터를 수집·가공·적재하고, 자체 `lawdigest-pipeline` 런타임으로 상태 동기화와 AI 요약 실행을 오케스트레이션합니다.

### `services/ai` — AI 서비스
두 가지 책임을 가집니다.
- **`processor/`**: DB에 적재된 법안을 Gemini CLI 실시간 요약으로 처리하고, 장애 시 Codex CLI fallback 수행
- **`rag/`**: Qdrant 벡터 DB와 LLM을 결합한 법안 RAG 챗봇

<br>

## 데이터 파이프라인

현재 표준 실행 경로는 Airflow가 아니라 자체 `lawdigest-pipeline` 런타임입니다.

| 명령 | 역할 |
|------|------|
| `bill-ingest` | 국회 API → 정제 artifact → DB 법안 수집 |
| `bill-status-sync` | 의원·lifecycle·vote 상태 동기화 |
| `ai-summary` | Gemini CLI 기반 실시간 요약, Codex CLI fallback |
| `ai-batch-submit` / `ai-batch-ingest` | legacy Batch API fallback |

자세한 구조와 운영 명령은 [데이터 파이프라인 아키텍처](docs/data/법안%20데이터%20파이프라인/pipeline_architecture.md)와 [런타임 런북](docs/data/법안%20데이터%20파이프라인/pipeline_restart_runbook.md)을 기준으로 합니다.

<br>

## 로컬 실행

### 인프라 (Docker)

```bash
docker-compose up -d mysql redis
```

### 백엔드

```bash
cd services/backend
./gradlew bootRun
```

### 프론트엔드

```bash
cd services/web
npm install
npm run dev
```

### AI 서비스

```bash
cd services/ai
pip install -e .
```

> 환경변수 설정이 필요합니다. OpenAI API 키, DB 접속 정보, Qdrant 호스트 등을 `.env` 파일에 설정하세요.

<br>

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
