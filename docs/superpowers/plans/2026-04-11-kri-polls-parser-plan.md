# 코리아리서치인터내셔널 여론조사 파서 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `(주)코리아리서치인터내셔널` PDF 58건을 전용 메인 파서 1개로 처리하고 `unparseable` 상태에서 제거한다.

**Architecture:** `parser.py`에는 기관 전용 `parse()` 파서만 추가하고, ASCII-art 텍스트 표 복원 로직은 `text_table_utils.py`로 분리한다. 파서는 `full_text`를 메인 입력으로 사용하고, `fitz words`는 열 경계 보정 fallback으로만 사용한다.

**Tech Stack:** Python 3, pytest, PyMuPDF(fitz), json, logging

---

## 파일 구조 맵

- Create: `services/data/src/lawdigest_data/polls/text_table_utils.py`
  - ASCII-art 텍스트 표 정규화/블록 추출/헤더 병합/열 경계 보정 유틸
- Modify: `services/data/src/lawdigest_data/polls/parser.py`
  - `_KoreaResearchInternationalParser` 추가
- Modify: `services/data/config/parser_registry.json`
  - 기관 등록 추가 및 `unparseable` 제거
- Create: `services/data/tests/polls/test_text_table_utils.py`
  - 텍스트 표 유틸 단위 테스트
- Modify: `services/data/tests/polls/test_parser_validation_unit.py`
  - 코리아리서치인터내셔널용 검증 케이스 보강 필요 시 추가
- Create/Modify: `services/data/tests/polls/fixtures/*.json`
  - 대표 지역 PDF fixture

## Task 1: 텍스트 표 유틸 TDD

**Files:**
- Create: `services/data/src/lawdigest_data/polls/text_table_utils.py`
- Create: `services/data/tests/polls/test_text_table_utils.py`

- [ ] **Step 1: 실패 테스트 작성**

서울 샘플에서 발췌한 헤더/전체행 문자열로 아래 동작을 검증하는 테스트를 먼저 작성한다.

- 구분선 블록 추출
- 멀티라인 헤더 병합
- 전체 행에서 사례수/비율 추출
- 선택지 수와 비율 수 정렬

- [ ] **Step 2: 실패 확인**

Run: `cd services/data && pytest tests/polls/test_text_table_utils.py -v`
Expected: FAIL because module/functions do not exist

- [ ] **Step 3: 최소 구현**

`normalize_ascii_table_text()`, `extract_ascii_table_blocks()`, `merge_header_lines()`, `parse_total_row()` 수준의 최소 유틸을 구현한다.

- [ ] **Step 4: 테스트 재실행**

Run: `cd services/data && pytest tests/polls/test_text_table_utils.py -v`
Expected: PASS

## Task 2: 파서 클래스 TDD

**Files:**
- Modify: `services/data/src/lawdigest_data/polls/parser.py`
- Modify/Create: `services/data/tests/polls/test_parser_validation_unit.py`

- [ ] **Step 1: 코리아리서치인터내셔널 샘플 PDF 직접 파싱 테스트 작성**

서울 샘플 PDF를 대상으로 `PollResultParser().parse_pdf(...)`가 최소 1개 이상 질문을 반환하고, 첫 질문 결과가 validation 친화적 구조를 갖는 테스트를 작성한다.

- [ ] **Step 2: 실패 확인**

Run: `cd services/data && pytest tests/polls/test_parser_validation_unit.py -k korea -v`
Expected: FAIL with `UnknownPollsterError` or empty parse result

- [ ] **Step 3: 최소 구현**

`_KoreaResearchInternationalParser`를 추가해:

- `NEEDS_FITZ_WORDS = True`
- `문N`/`<표 N>` 탐지
- `full_text` 기준 ASCII-art 표 파싱
- 필요 시 words 좌표 보정

을 구현한다.

- [ ] **Step 4: 테스트 재실행**

Run: `cd services/data && pytest tests/polls/test_parser_validation_unit.py -k korea -v`
Expected: PASS

## Task 3: 기관 등록과 fixture 검증

**Files:**
- Modify: `services/data/config/parser_registry.json`
- Create/Modify: `services/data/tests/polls/fixtures/*.json`
- Modify: `services/data/tests/polls/test_parser_integration.py`

- [ ] **Step 1: registry/fixture 실패 케이스 준비**

코리아리서치인터내셔널 fixture가 없거나 registry가 미등록 상태임을 확인한다.

- [ ] **Step 2: 실패 확인**

Run: `cd services/data && pytest tests/polls/test_parser_integration.py -k '코리아리서치 or KoreaResearch' -v`
Expected: FAIL or zero matched cases

- [ ] **Step 3: registry 및 fixture 추가**

- `parser_registry.json`에 기관 등록
- `unparseable`에서 기관 제거
- 대표 지역 PDF fixture 생성 및 통합 테스트 집합 반영

- [ ] **Step 4: 통합 테스트 실행**

Run: `cd services/data && pytest tests/polls/test_parser_integration.py -v`
Expected: PASS with new fixture included

## Task 4: 전체 58건 probe 검증

**Files:**
- Modify as needed: `services/data/src/lawdigest_data/polls/text_table_utils.py`
- Modify as needed: `services/data/src/lawdigest_data/polls/parser.py`
- Modify as needed: `services/data/tests/polls/fixtures/*.json`

- [ ] **Step 1: 전체 probe 실행**

Run: `cd services/data && python3 scripts/polls/probe_parsers.py --pollster '(주)코리아리서치인터내셔널'`
Expected: initially some failures may remain

- [ ] **Step 2: 남은 변형 패턴 보완**

probe 실패 로그를 보고 열 경계, 헤더 병합, 지역별 변형만 최소 수정한다.

- [ ] **Step 3: probe 재실행**

Run: `cd services/data && python3 scripts/polls/probe_parsers.py --pollster '(주)코리아리서치인터내셔널'`
Expected: 58건 전부 성공

- [ ] **Step 4: coverage 반영 확인**

Run: `cd services/data && python3 scripts/polls/analyze_parser_coverage.py`
Expected: 코리아리서치인터내셔널이 `unparseable`가 아니라 성공 파서로 집계됨

## Task 5: 최종 검증

**Files:**
- Modify if needed: `services/data/docs/parser_development_status.md`

- [ ] **Step 1: lint 실행**

Run: `cd services/data && python3 -m pytest tests/polls/test_text_table_utils.py tests/polls/test_parser_validation_unit.py tests/polls/test_parser_integration.py -v`
Expected: PASS

- [ ] **Step 2: 프로젝트 표준 lint 또는 관련 검증 실행**

Run: `npm run lint` 또는 저장소의 Python lint 명령이 있으면 해당 명령
Expected: PASS

- [ ] **Step 3: 문서/현황 반영**

코리아리서치인터내셔널이 더 이상 `unparseable`이 아님을 현황 문서에 반영한다.
