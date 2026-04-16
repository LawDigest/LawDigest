# Plan: 선거 데이터 수집 파이프라인 구축

**Generated**: 2026-04-10
**Estimated Complexity**: High
**Target**: 제9회 전국동시지방선거 (sgId: 20220601)

## Overview

중앙선거관리위원회 OpenAPI 5개 서비스를 활용하여 선거 데이터(코드정보, 후보자, 당선인, 선거공약, 정당정책)를 수집·저장하는 파이프라인을 구축한다.

**핵심 설계 원칙:**
- SQLAlchemy ORM 도입 (기존 pymysql 직접 사용에서 전환)
- 기존 의안(bills) DataFetcher의 매퍼 기반 API 추상화 패턴 재활용
- 여론조사(polls) 데이터와 조인 가능한 스키마 설계
- DAG 기반 자동 수집을 위한 구조 (현 단계에서는 수동 실행)
- LLM 요약 및 벡터 임베딩 확장 고려

**API 호출 의존관계 (DAG):**
```
코드정보(선거코드)
    ├── 코드정보(선거구코드) ──┐
    ├── 코드정보(구시군코드)   ├── 후보자정보 ──┬── 선거공약정보
    ├── 코드정보(정당코드)     │               └── 당선인정보
    ├── 코드정보(직업코드)    ─┘
    └── 코드정보(학력코드)    ─┘                    정당정책정보
                                                      ↑
                                              코드정보(정당코드)
```

## Prerequisites

- Python 3.10+, SQLAlchemy 2.x, pymysql, requests, python-dotenv
- 공공데이터포털 API 키 (`APIKEY_DATAGOKR` in `.env`)
- MySQL DB 접속 정보 (`DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`)
- 기존 프로젝트 구조: `services/data/src/lawdigest_data/`

---

## Sprint 1: 기반 인프라 — SQLAlchemy + API 클라이언트

**Goal**: ORM 모델 정의 + 범용 API 클라이언트 구축 + 코드정보 수집

**Demo/Validation**:
- `python -m scripts.elections.collect_codes` 실행 → 선거코드, 선거구, 정당 등 코드 데이터 DB 저장 확인
- SQLAlchemy 모델로 쿼리하여 데이터 조회 확인

### Task 1.1: SQLAlchemy 기반 DB 엔진 설정

- **Location**: `services/data/src/lawdigest_data/elections/database.py`
- **Description**:
  - `.env`에서 DB 접속 정보 로딩
  - SQLAlchemy `engine`, `SessionLocal`, `Base` 설정
  - 기존 connectors/DatabaseManager와 공존 가능하도록 독립 모듈
- **Dependencies**: 없음
- **Acceptance Criteria**:
  - `create_engine()` 으로 MySQL 연결 성공
  - `Base.metadata.create_all()` 으로 테이블 자동 생성
- **Validation**:
  - 임포트 후 세션 생성/종료 테스트

### Task 1.2: 코드정보 ORM 모델 정의

- **Location**: `services/data/src/lawdigest_data/elections/models/codes.py`
- **Description**:
  - `ElectionCode` — 선거코드 (sgId, sgTypecode, sgName, sgVotedate)
  - `DistrictCode` — 선거구코드 (sgId, sgTypecode, sggName, sdName, wiwName, sggJungsu)
  - `GusigunCode` — 구시군코드 (sgId, sdName, wiwName)
  - `PartyCode` — 정당코드 (sgId, jdName)
  - `JobCode` — 직업코드 (sgId, jobId, jobName)
  - `EduCode` — 학력코드 (sgId, eduId, eduName)
  - 각 모델에 created_at, updated_at 타임스탬프
- **Dependencies**: Task 1.1
- **Acceptance Criteria**:
  - 모든 모델이 Base를 상속
  - 적절한 PK, UNIQUE 제약 설정
  - 선거종류코드 Enum 정의 (1~11)
- **Validation**:
  - `create_all()` 후 MySQL에 테이블 6개 생성 확인

### Task 1.3: 중앙선거관리위원회 API 클라이언트

- **Location**: `services/data/src/lawdigest_data/elections/api_client.py`
- **Description**:
  - `NecApiClient` 클래스 — 기존 bills DataFetcher의 매퍼 패턴 참고
  - Base URL: `http://apis.data.go.kr/9760000/`
  - 공통 기능: serviceKey 자동 주입, 페이지네이션 자동 처리, XML/JSON 응답 파싱
  - HTTPAdapter + Retry(3회, 지수 백오프) 설정
  - 결과코드(resultCode) 검증 및 에러 핸들링
  - `fetch_all_pages(service, operation, params) -> list[dict]` 제네릭 메서드
  - rate limiting (초당 30tps 준수)
- **Dependencies**: 없음
- **Acceptance Criteria**:
  - 단일 메서드로 모든 API 오퍼레이션 호출 가능
  - 페이지네이션 자동 처리 (numOfRows=100씩)
  - 에러 시 재시도 후 실패하면 예외 발생
- **Validation**:
  - `getCommonSgCodeList` 실제 호출하여 선거코드 목록 반환 확인

### Task 1.4: 코드정보 수집기

- **Location**: `services/data/src/lawdigest_data/elections/collectors/code_collector.py`
- **Description**:
  - `CodeCollector` 클래스 — NecApiClient를 사용하여 6개 코드 오퍼레이션 순차 호출
  - API 응답 → ORM 모델 변환 → DB upsert
  - 수집 순서: 선거코드 → (구시군코드, 선거구코드, 정당코드, 직업코드, 학력코드) 병렬 가능
  - sgId 필터링 (제9회 지방선거만)
- **Dependencies**: Task 1.2, Task 1.3
- **Acceptance Criteria**:
  - 6개 코드 테이블에 데이터 적재 완료
  - 중복 실행 시 upsert (기존 데이터 갱신)
- **Validation**:
  - DB에서 SELECT로 코드 데이터 존재 확인
  - 제9회 지방선거 sgId 값 확인

### Task 1.5: 코드 수집 실행 스크립트

- **Location**: `services/data/scripts/elections/collect_codes.py`
- **Description**:
  - CLI 진입점 스크립트
  - `--sg-id` 옵션으로 대상 선거 지정 (기본값: 제9회 지방선거)
  - tqdm 진행률 표시
  - 로깅 설정 (logger)
- **Dependencies**: Task 1.4
- **Acceptance Criteria**:
  - `python -m scripts.elections.collect_codes` 실행 성공
  - 진행률 및 결과 요약 로그 출력
- **Validation**:
  - 실행 후 DB 테이블 데이터 건수 확인

---

## Sprint 2: 후보자 + 당선인 데이터 수집

**Goal**: 후보자(예비/확정) 및 당선인 정보 수집 + 여론조사 연계 키 설계

**Demo/Validation**:
- `python -m scripts.elections.collect_candidates` 실행 → 후보자/당선인 DB 저장
- 여론조사 데이터와 region/election_name 기준 조인 쿼리 테스트

### Task 2.1: 후보자/당선인 ORM 모델 정의

- **Location**: `services/data/src/lawdigest_data/elections/models/candidates.py`
- **Description**:
  - `Candidate` (예비후보자 + 후보자 통합)
    - huboid(후보자ID), sgId, sgTypecode, sggName, sdName, wiwName
    - giho, jdName, name, hanjaName, gender, birthday, age
    - addr, jobId, job, eduId, edu, career1, career2
    - regdate, status(등록/사퇴/사망/등록무효)
    - candidate_type ENUM ('preliminary', 'confirmed') — 예비/확정 구분
  - `Winner` (당선인)
    - 위 Candidate 필드 + dugsu(득표수), dugyul(득표율)
    - candidate_id FK로 Candidate 연결
  - **여론조사 연계 필드**:
    - `normalized_region` — polls.PollSurvey.region과 조인 가능한 정규화 지역명
    - `normalized_election_name` — polls.PollSurvey.election_name과 조인 가능한 선거명
- **Dependencies**: Task 1.2
- **Acceptance Criteria**:
  - Candidate-Winner 1:0..1 관계
  - polls 테이블과 조인 가능한 정규화 필드 존재
- **Validation**:
  - 테이블 생성 확인, 외래키 관계 확인

### Task 2.2: 지역명/선거명 정규화 유틸

- **Location**: `services/data/src/lawdigest_data/elections/utils/normalizer.py`
- **Description**:
  - API 응답의 sdName/sggName → polls의 region 매핑
    - 예: "서울특별시" → "서울특별시 전체"
    - 예: "경기도" → "경기도 전체"
  - sgTypecode → election_name 매핑
    - 예: 3(시도지사) → "광역단체장선거"
    - 예: 4(구시군장) → "기초단체장선거"
  - 매핑 테이블은 상수 dict로 관리
- **Dependencies**: 없음
- **Acceptance Criteria**:
  - 모든 시도명이 정규화 가능
  - 매핑 실패 시 경고 로그 + 원본 값 유지
- **Validation**:
  - 단위 테스트로 주요 매핑 확인

### Task 2.3: 후보자/당선인 수집기

- **Location**: `services/data/src/lawdigest_data/elections/collectors/candidate_collector.py`
- **Description**:
  - `CandidateCollector` — DB에서 선거구코드 로딩 → 선거구별 후보자 API 호출
  - 수집 순서: 선거종류코드별 → 시도별 → 선거구별
  - 예비후보자(`getPoelpcddRegistSttusInfoInqire`) + 후보자(`getPofelcddRegistSttusInfoInqire`) 순차
  - `WinnerCollector` — 동일 패턴으로 당선인 정보 수집
  - 수집 시 정규화 유틸 적용하여 normalized 필드 자동 계산
  - 진행률 로깅 (tqdm)
- **Dependencies**: Task 2.1, Task 2.2, Sprint 1
- **Acceptance Criteria**:
  - 제9회 지방선거 전체 후보자/당선인 수집 완료
  - 중복 실행 시 upsert
- **Validation**:
  - DB에서 후보자 건수 확인
  - 여론조사 region과 조인 쿼리 성공

### Task 2.4: 후보자/당선인 수집 실행 스크립트

- **Location**: `services/data/scripts/elections/collect_candidates.py`
- **Description**:
  - CLI 진입점: `--sg-id`, `--type` (preliminary/confirmed/winner/all) 옵션
  - 코드정보 수집 완료 여부 사전 확인
  - 진행률 + ETA 로깅
- **Dependencies**: Task 2.3
- **Acceptance Criteria**:
  - 단일 명령으로 전체 후보자+당선인 수집 가능
- **Validation**:
  - 실행 후 DB 확인

---

## Sprint 3: 선거공약 + 정당정책 수집

**Goal**: 공약/정책 텍스트 수집 + LLM 요약/임베딩 확장 기반 마련

**Demo/Validation**:
- `python -m scripts.elections.collect_pledges` 실행 → 공약/정책 DB 저장
- 특정 후보자의 공약 텍스트 조회 쿼리 확인

### Task 3.1: 공약/정책 ORM 모델 정의

- **Location**: `services/data/src/lawdigest_data/elections/models/pledges.py`
- **Description**:
  - `ElectionPledge` (선거공약)
    - candidate_id FK → Candidate
    - sgId, sgTypecode, cnddtId(huboid)
    - prmsOrd(공약순서, 1~10)
    - prmsTitle(공약제목), prmsContent(공약내용)
    - 정규화 필드 (region, election_name)
  - `PartyPolicy` (정당정책)
    - sgId, partyName
    - prmsCnt(정책수)
    - prmsOrd(정책순서, 1~10)
    - prmsTitle, prmsContent
  - **LLM 확장 대비 필드**:
    - `summary` (TEXT, nullable) — 추후 LLM 요약 저장용
    - `embedding_id` (VARCHAR, nullable) — 벡터 임베딩 참조용
  - 주의: 선거공약은 sgTypecode 1,3,4,11만 제공
- **Dependencies**: Task 2.1
- **Acceptance Criteria**:
  - Candidate와 FK 관계 설정
  - 공약 최대 10건 구조 반영
- **Validation**:
  - 테이블 생성 확인

### Task 3.2: 공약/정책 수집기

- **Location**: `services/data/src/lawdigest_data/elections/collectors/pledge_collector.py`
- **Description**:
  - `PledgeCollector` — DB에서 후보자 목록 로딩 → 후보자별 공약 API 호출
  - sgTypecode 필터링 (1,3,4,11만)
  - `PartyPolicyCollector` — DB에서 정당 목록 로딩 → 정당별 정책 API 호출
  - 진행률 로깅, rate limiting
- **Dependencies**: Task 3.1, Sprint 2
- **Acceptance Criteria**:
  - 제9회 지방선거 전체 공약/정책 수집 완료
- **Validation**:
  - DB에서 공약 건수 확인

### Task 3.3: 공약/정책 수집 실행 스크립트

- **Location**: `services/data/scripts/elections/collect_pledges.py`
- **Description**:
  - CLI 진입점: `--sg-id`, `--type` (pledge/policy/all) 옵션
  - 후보자 수집 완료 여부 사전 확인
- **Dependencies**: Task 3.2
- **Acceptance Criteria**:
  - 단일 명령으로 전체 공약+정책 수집 가능
- **Validation**:
  - 실행 후 DB 확인

---

## Sprint 4: 통합 파이프라인 + 검증

**Goal**: 전체 수집 워크플로우 통합, 데이터 검증, 여론조사 연계 확인

**Demo/Validation**:
- `python -m scripts.elections.collect_all` 실행 → 전체 파이프라인 자동 실행
- 여론조사-후보자-당선인-공약 연계 쿼리 성공

### Task 4.1: 통합 수집 오케스트레이터

- **Location**: `services/data/src/lawdigest_data/elections/pipeline.py`
- **Description**:
  - `ElectionPipeline` 클래스 — DAG 순서에 따라 수집기 순차 실행
  - 단계별 상태 추적 (코드 → 후보자 → 당선인 → 공약 → 정책)
  - 체크포인트: 각 단계 완료 시 상태 기록, 실패 시 해당 단계부터 재시작
  - 수집 결과 요약 리포트 출력
- **Dependencies**: Sprint 1~3
- **Acceptance Criteria**:
  - 단일 명령으로 전체 파이프라인 실행 가능
  - 부분 실패 시 재시작 가능
- **Validation**:
  - 전체 실행 후 모든 테이블 데이터 건수 확인

### Task 4.2: 데이터 검증 모듈

- **Location**: `services/data/src/lawdigest_data/elections/validation.py`
- **Description**:
  - 수집 후 데이터 무결성 검증:
    - 선거구별 후보자 수 vs 당선인 수 (정수 검증: sggJungsu == 당선인 수)
    - 후보자 중 status='등록'인 건 vs 공약 존재 여부
    - 정당코드에 있는 정당 vs 정당정책 존재 여부
    - NULL/빈값 비율 통계
  - 검증 결과 리포트 (JSON + 콘솔 출력)
- **Dependencies**: Sprint 1~3
- **Acceptance Criteria**:
  - 검증 통과 기준 정의 및 경고/에러 구분
- **Validation**:
  - 의도적 결함 데이터로 검증 로직 테스트

### Task 4.3: 여론조사 연계 쿼리 모듈

- **Location**: `services/data/src/lawdigest_data/elections/queries.py`
- **Description**:
  - 여론조사-후보자 연계 쿼리 함수 모음:
    - `get_candidates_with_polls(region, election_name)` — 특정 지역 후보자 + 여론조사 결과
    - `get_winner_vs_polls(region)` — 당선인 득표율 vs 여론조사 예측치
  - SQLAlchemy 쿼리 + 기존 pymysql polls 테이블 조인
  - pandas DataFrame 반환
- **Dependencies**: Task 4.1
- **Acceptance Criteria**:
  - 서울특별시 광역단체장 후보자 + 여론조사 조인 성공
- **Validation**:
  - 쿼리 결과 DataFrame 출력 확인

### Task 4.4: 통합 실행 스크립트

- **Location**: `services/data/scripts/elections/collect_all.py`
- **Description**:
  - CLI 진입점: `--sg-id`, `--skip-codes`, `--validate` 옵션
  - 전체 파이프라인 실행 + 검증 + 결과 리포트
- **Dependencies**: Task 4.1, Task 4.2
- **Acceptance Criteria**:
  - 단일 명령으로 수집~검증 완료
- **Validation**:
  - 처음부터 끝까지 실행 성공

---

## 디렉토리 구조 (최종)

```
services/data/
├── src/lawdigest_data/
│   ├── elections/
│   │   ├── __init__.py
│   │   ├── database.py          # SQLAlchemy 엔진/세션 설정
│   │   ├── api_client.py        # NecApiClient (범용 API 클라이언트)
│   │   ├── pipeline.py          # ElectionPipeline (오케스트레이터)
│   │   ├── validation.py        # 데이터 검증
│   │   ├── queries.py           # 여론조사 연계 쿼리
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── codes.py         # 코드정보 6종 ORM
│   │   │   ├── candidates.py    # 후보자/당선인 ORM
│   │   │   └── pledges.py       # 공약/정책 ORM
│   │   ├── collectors/
│   │   │   ├── __init__.py
│   │   │   ├── code_collector.py
│   │   │   ├── candidate_collector.py
│   │   │   └── pledge_collector.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── normalizer.py    # 지역명/선거명 정규화
│   ├── bills/  (기존)
│   ├── polls/  (기존)
│   └── connectors/  (기존)
├── scripts/elections/
│   ├── collect_codes.py
│   ├── collect_candidates.py
│   ├── collect_pledges.py
│   └── collect_all.py
└── config/
    └── election_config.json     # 선거 타입 매핑, 정규화 테이블 등
```

## 테이블 구조 요약

```
election_codes          ← 선거코드 (sgId, sgTypecode, sgName, sgVotedate)
election_districts      ← 선거구코드 (sgId, sgTypecode, sggName, sdName, wiwName)
election_gusiguns       ← 구시군코드 (sgId, sdName, wiwName)
election_parties        ← 정당코드 (sgId, jdName)
election_jobs           ← 직업코드 (sgId, jobId, jobName)
election_educations     ← 학력코드 (sgId, eduId, eduName)
election_candidates     ← 후보자 (huboid, sgId, candidate_type, normalized_region, ...)
election_winners        ← 당선인 (candidate FK, dugsu, dugyul)
election_pledges        ← 선거공약 (candidate FK, prmsOrd, prmsTitle, prmsContent)
election_party_policies ← 정당정책 (sgId, partyName, prmsOrd, prmsTitle, prmsContent)

(기존) poll_surveys     ← 여론조사 (region, election_name으로 연계)
(기존) poll_questions   ← 설문문항
(기존) poll_options     ← 응답선택지
```

## Testing Strategy

- **Sprint 1**: 코드정보 API 실제 호출 → DB 저장 → SELECT 확인
- **Sprint 2**: 후보자/당선인 수집 → 건수 확인 → 여론조사 조인 테스트
- **Sprint 3**: 공약/정책 수집 → 후보자-공약 FK 관계 확인
- **Sprint 4**: 전체 파이프라인 → 검증 모듈 → 연계 쿼리 통합 테스트

## Potential Risks & Gotchas

1. **API Rate Limiting**: 초당 30tps 제한 → 선거구별 호출 시 sleep 필요
2. **sgId 값**: 제9회 지방선거 sgId가 문서에 없음 → Sprint 1에서 실제 API 호출로 확인 필요
3. **데이터 부재**: 역대선거로 이동된 선거는 주소 미제공, 선거공약은 sgTypecode 1,3,4,11만
4. **여론조사 연계**: 지역명 정규화 매핑이 완벽하지 않을 수 있음 (테스트 필수)
5. **SQLAlchemy 도입**: 기존 pymysql 코드와 혼재 → 세션 관리 충돌 주의
6. **예비후보자 특수성**: 후보자등록 개시일부터 조회 불가 → 이미 지난 선거라 문제 없을 수 있으나 확인 필요

## Rollback Plan

- SQLAlchemy 테이블은 독립적 (`election_*` prefix) → 기존 테이블 영향 없음
- 문제 발생 시 `election_*` 테이블 DROP으로 깨끗하게 복원 가능
- 기존 polls/bills 코드에 변경 없음 (순수 추가)
