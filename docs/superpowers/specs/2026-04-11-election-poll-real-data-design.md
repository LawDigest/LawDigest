# 선거-여론조사 탭 실데이터 연동 설계

- **작성일:** 2026-04-11
- **대상:** `services/web/app/election/`, `services/backend/src/main/java/com/everyones/lawmaking/`
- **목표:** 선거-여론조사 탭을 실제 `PollSurvey / PollQuestion / PollOption` 데이터에 연결하고, 선택된 선거/지역 기준으로 일반화한다.

---

## 1. 배경

현재 `ElectionPollView`는 다음 목업 데이터 파일을 직접 읽는다.

- `mockPartyPollData.ts`
- `mockPollTimeseriesData.ts`
- `mockAgencyPollsData.ts`
- `mockPollData.ts`

반면 백엔드는 지도/후보/지역 패널 API만 제공하고, 여론조사 전용 조회 API는 없다. 데이터 파이프라인 쪽에서는 이미 `PollSurvey`, `PollQuestion`, `PollOption` 테이블로 실제 여론조사 데이터를 적재하고 있으므로, 이번 작업은 프론트 목업 제거와 백엔드 읽기 API 추가를 함께 수행한다.

---

## 2. 이번 작업의 확정 범위

사용자와 합의한 범위는 다음과 같다.

- 엔드투엔드 연결
  - 백엔드에 여론조사 전용 API를 추가하고 프론트 목업을 대체한다.
- 일반화 우선
  - 선택된 `election_id + region` 기준으로 동작하고, 데이터가 없는 조합은 빈 상태로 처리한다.
- 후보자별 탭 포함
  - `전체 / 정당별 / 지역별 / 후보자별` 네 서브탭 모두 실제 데이터 기반으로 동작시킨다.
- 권장안 채택
  - 선거 선택 상태는 전 탭 공통 상태로 끌어올린다.
  - 후보자별 탭은 `가상대결` 질문을 우선 사용하고, 없으면 `후보 적합도`로 fallback 한다.
  - 질문 분류는 코드 규칙 + 예외 매핑 파일 1개 방식으로 운영한다.

---

## 3. 상위 구조

### 3.1 프론트 상태

`ElectionMapShell`이 다음 두 상태를 공통으로 소유한다.

- `selectedElectionId`
- `confirmedRegion`

이 상태를 다음 하위 탭에 공통 props 또는 공유 훅으로 전달한다.

- `ElectionMapTabView`
- `ElectionFeedView`
- `ElectionPollView`
- `ElectionDistrictView`

이 구조를 택하는 이유는 여론조사 탭만 고정된 지방선거를 사용하는 현재 방식으로는 일반화 요구와 충돌하기 때문이다.

### 3.2 백엔드 책임 분리

기존 `ElectionService`에 여론조사 로직을 직접 누적하지 않고, 여론조사 조회 전용 서비스 계층을 분리한다.

예상 구성:

- `ElectionPollController` 또는 `ElectionController` 하위 poll 엔드포인트 추가
- `PollQueryService`
- `PollNormalizationService`
- `PollQuestionClassifier`
- `Poll*Response` DTO
- `PollSurveyRepository`, `PollQuestionRepository`, `PollOptionRepository`

---

## 4. 데이터 모델 및 정규화

### 4.1 읽기 원본

원본 테이블은 다음 3개를 사용한다.

- `PollSurvey`
  - 조사 메타 정보, 기간, 표본수, 오차범위, 기관, 지역
- `PollQuestion`
  - 질문 번호, 질문 제목, 완료 표본
- `PollOption`
  - 선택지명, 비율

### 4.2 선거 정규화

프론트의 `election_id`와 poll DB의 `election_type` / `election_name` 표현은 일치하지 않을 수 있다. 따라서 서버에 선거 정규화 계층을 둔다.

역할:

- `election_id`를 받아 poll DB 검색 기준 문자열 세트로 변환
- 예: `local-2026` -> `제9회 전국동시지방선거`
- 필요 시 `ElectionCode` 조회 결과와 함께 선거군/선거명 보조 정보를 만든다.

### 4.3 지역 정규화

프론트의 `confirmedRegion`은 `regionCode + regionName` 구조이고, poll DB는 `"서울특별시 전체"`, `"경기도 전체"` 같은 문자열을 사용한다. 따라서 서버에서 poll DB용 지역 문자열을 계산한다.

예:

- `11 / 서울특별시` -> `서울특별시 전체`
- `41 / 경기도` -> `경기도 전체`

향후 구/군 단위 데이터가 추가되면 이 계층을 확장한다.

### 4.4 명칭 정규화

정당명/후보명은 조사기관별로 띄어쓰기, 약칭, 표기 흔들림이 존재한다. 이를 위한 예외 매핑 파일을 둔다.

예:

- `더불어 민주당` -> `더불어민주당`
- `김 동 연` -> `김동연`
- `없다/모름`, `없음/모름`, `잘 모름` -> `무응답 계열`

---

## 5. 질문 분류 규칙

서버는 `question_title`, `question_text`, `option_name`을 사용해 질문을 다음 중 하나로 분류한다.

- `PARTY_SUPPORT`
- `CANDIDATE_FIT`
- `MATCHUP`
- `OTHER`

### 5.1 PARTY_SUPPORT

다음 표현을 우선 탐지한다.

- `정당지지도`
- `지지정당`

이 질문은 다음 화면에 사용한다.

- 전체 탭의 정당 추이
- 전체 탭의 현재 정당 지지율
- 정당별 탭의 시계열/지역 분포
- 지역별 탭의 정당 스냅샷

### 5.2 CANDIDATE_FIT

다음 표현을 탐지한다.

- `후보 적합도`
- `후보 지지도`
- `누가 가장 적합`

이 질문은 다음 화면에 사용한다.

- 후보자별 탭 fallback 시계열
- 전체 탭 후보 블록 보조 데이터

### 5.3 MATCHUP

다음 표현을 탐지한다.

- `가상대결`
- `양자대결`
- `누구에게 투표`
- `맞붙는다면`

이 질문은 다음 화면에 사용한다.

- 후보자별 탭 기본 비교 시계열
- 전체 탭 후보 비교 블록
- 지역별 탭 후보 스냅샷

### 5.4 OTHER

정책, 국정평가, 지방선거 인식 등 위 3개에 속하지 않는 질문은 `OTHER`로 분류하고 여론조사 탭의 핵심 시각화에서는 제외한다. 분류 누락은 서버 로그에 남긴다.

---

## 6. 신규 API 설계

### 6.1 `GET /v1/election/polls/overview`

입력:

- `election_id`
- `region_code`

반환:

- 대표 요약 카드
  - `leading_party`
  - `runner_up_party`
  - `gap`
  - `undecided`
- 정당 추이 시계열
- 최신 정당 스냅샷
- 대표 후보 비교 블록
  - 진보/보수 적합도 또는 가상대결 기반
- 최신 조사 리스트
- 조사 카드 상세 리스트

### 6.2 `GET /v1/election/polls/party`

입력:

- `election_id`
- `party_name`

반환:

- `selected_party`
- `trend_series`
- `regional_distribution`
- `latest_surveys`

정당별 탭의 기존 UI를 유지하기 위해 프론트가 바로 순회 가능한 구조로 내려준다.

### 6.3 `GET /v1/election/polls/region`

입력:

- `election_id`
- `region_code`

반환:

- `region_summary`
- `party_snapshot`
- `candidate_snapshot`
- `latest_surveys`

지역별 탭의 `PollRegionPanel`을 실제 응답 기반으로 교체한다.

### 6.4 `GET /v1/election/polls/candidate`

입력:

- `election_id`
- `region_code`
- `candidate_name` (선택)

반환:

- `candidate_options`
- `selected_candidate`
- `basis_question_kind`
  - `MATCHUP` 또는 `CANDIDATE_FIT`
- `series`
- `comparison_series`
- `latest_snapshot`

기본 동작:

- `MATCHUP`이 존재하면 이를 우선 사용
- 없으면 `CANDIDATE_FIT`으로 fallback

---

## 7. 백엔드 집계 규칙

### 7.1 overview 집계

- 최신 조사 리스트는 조사 종료일 또는 등록일 기준 내림차순
- 정당 추이는 `PARTY_SUPPORT` 질문 중 정규화된 정당 옵션만 사용
- 무응답/기타 계열은 `undecided` 계산에 포함하되, 메인 순위에는 제외
- 후보 블록은 `MATCHUP` 우선, 없으면 `CANDIDATE_FIT`

### 7.2 party 집계

- 선택 정당의 최신 지역별 값은 동일 선거 내 여러 지역 조사에서 가장 최신 질문을 지역 단위로 뽑아 만든다.
- 동일 지역 최신값이 없으면 해당 지역은 분포에서 제외한다.

### 7.3 region 집계

- 선택 지역 기준으로 조사 리스트와 스냅샷을 구성한다.
- 같은 조사 내 여러 질문이 있으면 `PARTY_SUPPORT`, `CANDIDATE_FIT`, `MATCHUP`을 분리해 함께 묶는다.

### 7.4 candidate 집계

- `candidate_options`는 해당 지역 최신 조사들에서 나타난 후보명 집합으로 만든다.
- 선택 후보의 시계열은 같은 분류(`MATCHUP` 또는 `CANDIDATE_FIT`) 내에서만 연결한다.
- 비교 시계열은 같은 질문에 함께 등장한 주요 경쟁 후보를 기준으로 만든다.

---

## 8. 프론트 변경 설계

### 8.1 공통 query 추가

`services/web/app/election/apis`에 poll 전용 API와 query key를 추가한다.

예상 추가 항목:

- `getElectionPollOverview`
- `getElectionPollParty`
- `getElectionPollRegion`
- `getElectionPollCandidate`
- 대응 `useGet...` hooks

### 8.2 `ElectionPollView`

다음 목업 import를 제거한다.

- `MOCK_PARTY_POLL_DATA`
- `MOCK_POLL_TIMESERIES`
- `MOCK_AGENCY_POLLS`
- `POLL_SUMMARY`

대신 탭별 query를 사용한다.

- 전체 탭 -> `overview`
- 정당별 탭 -> `party`
- 지역별 탭 -> `region`
- 후보자별 탭 -> `candidate`

### 8.3 후보자별 탭

현재 `"준비 중"` 문구를 제거하고 다음 흐름으로 대체한다.

- 지역 선택
- 후보 목록 로딩
- 후보 선택 또는 기본 후보 자동 선택
- 시계열/비교 차트 렌더링

### 8.4 지역 상태 공유

`ElectionMapShell` 상단으로 `selectedElectionId`를 올리면서 poll 탭도 동일 상태를 사용하도록 조정한다. 이 작업은 여론조사 탭 실데이터 일반화의 필수 선행 조건이다.

---

## 9. 빈 상태 / 오류 / 로그

### 9.1 빈 상태

데이터가 없는 조합은 예외가 아니라 정상 응답으로 처리한다.

- overview: 빈 시계열 + 빈 리스트
- party: 빈 분포 + 빈 추이
- region: 빈 조사 리스트
- candidate: 빈 후보 옵션 + 빈 시계열

프론트는 기존 문구를 재사용한다.

### 9.2 오류 상태

다음은 서버 오류로 본다.

- DB 조회 실패
- 선거/지역 정규화 실패
- 분류기 예외

프론트는 기존 에러 문구를 유지한다.

### 9.3 로그

서버는 최소한 다음을 로그로 남긴다.

- 분류되지 않은 질문 수
- 정규화 실패한 후보/정당 표기
- 요청별 응답 건수

---

## 10. 테스트 전략

### 10.1 백엔드

- 질문 분류 단위 테스트
- 선거/지역 정규화 단위 테스트
- 각 endpoint 응답 shape 테스트
- `서울특별시`, `경기도` fixture 기반 집계 테스트

### 10.2 프론트

- 탭별 query 응답 렌더링 테스트
- 빈 상태 테스트
- 에러 상태 테스트
- 후보자별 탭 기본 fallback 테스트

---

## 11. 비범위

이번 작업 범위에 포함하지 않는다.

- poll 적재 파이프라인 구조 변경
- 신규 요약 테이블 생성
- 구/군 단위 지역 세분화 확장
- 지도 탭 자체의 실데이터 일반화
- 피드 탭의 실데이터 연동

---

## 12. 구현 순서 초안

1. poll 조회용 백엔드 entity/repository/service/DTO 추가
2. 질문 분류/정규화 계층 추가
3. poll API 4종 추가 및 테스트
4. 프론트 poll types/query/api 추가
5. `ElectionPollView`에서 목업 제거 후 실제 query 연동
6. `selectedElectionId` 공통 상태 승격
7. 프론트 테스트 보강
