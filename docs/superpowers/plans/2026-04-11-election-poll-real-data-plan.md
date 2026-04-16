# 선거-여론조사 탭 실데이터 연동 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 선거-여론조사 탭의 `전체 / 정당별 / 지역별 / 후보자별` 서브뷰를 실제 `PollSurvey / PollQuestion / PollOption` 데이터에 연결하고, 선택된 `election_id + region` 기준으로 일반화한다.

**Architecture:** 백엔드는 poll 원본 테이블을 직접 읽는 전용 조회 계층을 추가하고, 서버에서 질문을 `PARTY_SUPPORT / CANDIDATE_FIT / MATCHUP`으로 분류한 뒤 프론트 친화 DTO를 반환한다. 프론트는 `ElectionMapShell`에 `selectedElectionId`를 공통 상태로 끌어올리고, `ElectionPollView`의 목업 import를 제거한 뒤 React Query로 네 개의 poll endpoint를 구독한다.

**Tech Stack:** Spring Boot 3, Spring Data JPA, JUnit 5, Next.js 14, React 18, React Query 5, Vitest, Testing Library

---

## 실행 전제

- 구현 시작 시점에만 브랜치를 만든다.
- 브랜치 규칙은 `feat/election-poll-real-data/codex`를 기본안으로 사용한다.
- 사용자가 원하면 `.worktrees/` 아래 전용 worktree를 만든다.
- 기존 작업 트리에 미정리 변경이 있으므로, 구현 단계에서는 worktree 사용 여부를 먼저 사용자에게 확인한다.

## 파일 구조 맵

- Create: `services/backend/src/main/java/com/everyones/lawmaking/domain/entity/poll/PollSurvey.java`
  - poll 메타 정보 read-only JPA entity
- Create: `services/backend/src/main/java/com/everyones/lawmaking/domain/entity/poll/PollQuestion.java`
  - 질문 메타 read-only JPA entity
- Create: `services/backend/src/main/java/com/everyones/lawmaking/domain/entity/poll/PollOption.java`
  - 선택지 비율 read-only JPA entity
- Create: `services/backend/src/main/java/com/everyones/lawmaking/repository/poll/PollSurveyRepository.java`
  - 선거/지역 기준 survey 조회
- Create: `services/backend/src/main/java/com/everyones/lawmaking/repository/poll/PollQuestionRepository.java`
  - survey 질문 조회
- Create: `services/backend/src/main/java/com/everyones/lawmaking/repository/poll/PollOptionRepository.java`
  - question 선택지 조회
- Create: `services/backend/src/main/java/com/everyones/lawmaking/service/election/poll/PollQuestionClassifier.java`
  - 질문 분류 규칙
- Create: `services/backend/src/main/java/com/everyones/lawmaking/service/election/poll/PollNormalizationService.java`
  - 선거/지역/정당/후보명 정규화
- Create: `services/backend/src/main/java/com/everyones/lawmaking/service/election/poll/PollQueryService.java`
  - overview/party/region/candidate 집계 오케스트레이션
- Create: `services/backend/src/main/java/com/everyones/lawmaking/common/dto/response/election/ElectionPollOverviewResponse.java`
  - 전체 탭 응답
- Create: `services/backend/src/main/java/com/everyones/lawmaking/common/dto/response/election/ElectionPollPartyResponse.java`
  - 정당별 탭 응답
- Create: `services/backend/src/main/java/com/everyones/lawmaking/common/dto/response/election/ElectionPollRegionResponse.java`
  - 지역별 탭 응답
- Create: `services/backend/src/main/java/com/everyones/lawmaking/common/dto/response/election/ElectionPollCandidateResponse.java`
  - 후보자별 탭 응답
- Modify: `services/backend/src/main/java/com/everyones/lawmaking/controller/ElectionController.java`
  - `/v1/election/polls/*` endpoint 4개 추가
- Modify: `services/backend/src/main/java/com/everyones/lawmaking/service/election/ElectionService.java`
  - poll 상태 승격이 필요 없으면 미수정, 필요 시 selector/shared 상태 연결만 최소 반영
- Create: `services/backend/src/test/java/com/everyones/lawmaking/service/election/poll/PollQuestionClassifierTest.java`
  - 분류 규칙 단위 테스트
- Create: `services/backend/src/test/java/com/everyones/lawmaking/service/election/poll/PollNormalizationServiceTest.java`
  - 선거/지역/명칭 정규화 테스트
- Create: `services/backend/src/test/java/com/everyones/lawmaking/service/election/poll/PollQueryServiceTest.java`
  - overview/party/region/candidate 집계 테스트
- Create: `services/backend/src/test/java/com/everyones/lawmaking/controller/ElectionPollControllerTest.java`
  - request param 매핑과 응답 serialization 테스트
- Modify: `services/web/types/type/election/election.ts`
  - poll 응답 타입 추가
- Modify: `services/web/app/election/apis/contracts.ts`
  - poll query key 계약 추가
- Modify: `services/web/app/election/apis/apis.ts`
  - poll API 함수 추가
- Modify: `services/web/app/election/apis/queries.ts`
  - poll React Query hook 추가
- Modify: `services/web/app/election/components/ElectionMapShell.tsx`
  - `selectedElectionId` 공통 상태 승격
- Modify: `services/web/app/election/components/ElectionPollView.tsx`
  - 목업 제거 및 실데이터 매핑
- Modify: `services/web/app/election/components/PollRegionPanel.tsx`
  - region endpoint 기반 패널 렌더링
- Create: `services/web/app/election/components/ElectionCandidatePollPanel.tsx`
  - 후보자별 시계열/비교 패널 분리
- Modify: `services/web/app/election/components/ElectionPollView.test.tsx`
  - 실데이터 hook mock 기반 렌더링 테스트
- Create: `services/web/app/election/components/ElectionCandidatePollPanel.test.tsx`
  - 후보자 fallback / 선택 로직 테스트
- Modify: `docs/superpowers/specs/2026-04-11-election-poll-real-data-design.md`
  - 구현 중 차이가 나면 설계 보정 메모만 최소 반영

## Task 1: 구현 작업대 준비

**Files:**
- Create/Use: `.worktrees/<name>` 또는 현재 저장소 새 브랜치

- [ ] **Step 1: 사용자에게 worktree 사용 여부 확인**

질문: `코드 작업을 별도 worktree(.worktrees/...)에서 진행할까요, 아니면 현재 저장소에서 새 브랜치만 만들까요?`

- [ ] **Step 2: 새 브랜치 생성**

Run: `git checkout -b feat/election-poll-real-data/codex`
Expected: branch switched successfully

- [ ] **Step 3: worktree 선택 시 worktree 생성**

Run: `git worktree add .worktrees/election-poll-real-data-codex -b feat/election-poll-real-data/codex`
Expected: new worktree created with branch checked out

- [ ] **Step 4: 작업 디렉토리에서 상태 확인**

Run: `git status --short`
Expected: worktree 또는 새 브랜치에서 예기치 않은 충돌 파일 없음

## Task 2: poll 분류/정규화 계층 TDD

**Files:**
- Create: `services/backend/src/main/java/com/everyones/lawmaking/service/election/poll/PollQuestionClassifier.java`
- Create: `services/backend/src/main/java/com/everyones/lawmaking/service/election/poll/PollNormalizationService.java`
- Create: `services/backend/src/test/java/com/everyones/lawmaking/service/election/poll/PollQuestionClassifierTest.java`
- Create: `services/backend/src/test/java/com/everyones/lawmaking/service/election/poll/PollNormalizationServiceTest.java`

- [ ] **Step 1: 실패 테스트 작성**

테스트에 최소 다음 케이스를 넣는다.

- `정당지지도` -> `PARTY_SUPPORT`
- `경기도지사 진보 후보 적합도` -> `CANDIDATE_FIT`
- `가상대결 A - 김동연 vs 양향자` -> `MATCHUP`
- `11 / 서울특별시` -> `서울특별시 전체`
- `더불어 민주당` -> `더불어민주당`
- `김 동 연` -> `김동연`

- [ ] **Step 2: 실패 확인**

Run: `cd services/backend && ./gradlew test --tests 'com.everyones.lawmaking.service.election.poll.PollQuestionClassifierTest' --tests 'com.everyones.lawmaking.service.election.poll.PollNormalizationServiceTest'`
Expected: FAIL because classes do not exist or rules are incomplete

- [ ] **Step 3: 최소 구현**

분류기와 정규화 서비스에 다음만 최소 구현한다.

- title/text 기반 분류
- 지역 코드 -> poll region label 매핑
- 선거 ID -> poll election label 매핑
- 정당/후보 alias map

- [ ] **Step 4: 테스트 재실행**

Run: `cd services/backend && ./gradlew test --tests 'com.everyones.lawmaking.service.election.poll.PollQuestionClassifierTest' --tests 'com.everyones.lawmaking.service.election.poll.PollNormalizationServiceTest'`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/backend/src/main/java/com/everyones/lawmaking/service/election/poll/PollQuestionClassifier.java \
        services/backend/src/main/java/com/everyones/lawmaking/service/election/poll/PollNormalizationService.java \
        services/backend/src/test/java/com/everyones/lawmaking/service/election/poll/PollQuestionClassifierTest.java \
        services/backend/src/test/java/com/everyones/lawmaking/service/election/poll/PollNormalizationServiceTest.java
git commit -m "feat: 여론조사 분류기와 정규화 계층 추가"
```

## Task 3: poll read-only entity/repository TDD

**Files:**
- Create: `services/backend/src/main/java/com/everyones/lawmaking/domain/entity/poll/PollSurvey.java`
- Create: `services/backend/src/main/java/com/everyones/lawmaking/domain/entity/poll/PollQuestion.java`
- Create: `services/backend/src/main/java/com/everyones/lawmaking/domain/entity/poll/PollOption.java`
- Create: `services/backend/src/main/java/com/everyones/lawmaking/repository/poll/PollSurveyRepository.java`
- Create: `services/backend/src/main/java/com/everyones/lawmaking/repository/poll/PollQuestionRepository.java`
- Create: `services/backend/src/main/java/com/everyones/lawmaking/repository/poll/PollOptionRepository.java`
- Modify: `services/backend/src/test/java/com/everyones/lawmaking/service/election/poll/PollQueryServiceTest.java`

- [ ] **Step 1: repository 소비 테스트 작성**

`PollQueryServiceTest`에 survey/question/option projection이 없어서 집계를 시작할 수 없는 상태를 먼저 드러내는 테스트를 작성한다.

- [ ] **Step 2: 실패 확인**

Run: `cd services/backend && ./gradlew test --tests 'com.everyones.lawmaking.service.election.poll.PollQueryServiceTest'`
Expected: FAIL because entities/repositories do not exist

- [ ] **Step 3: 최소 구현**

read-only entity와 repository를 만들고, 선거/지역 기준 survey 조회 + question/options 조회 메서드를 추가한다.

- [ ] **Step 4: 테스트 재실행**

Run: `cd services/backend && ./gradlew test --tests 'com.everyones.lawmaking.service.election.poll.PollQueryServiceTest'`
Expected: PASS or compile green for repository wiring stage

- [ ] **Step 5: Commit**

```bash
git add services/backend/src/main/java/com/everyones/lawmaking/domain/entity/poll \
        services/backend/src/main/java/com/everyones/lawmaking/repository/poll \
        services/backend/src/test/java/com/everyones/lawmaking/service/election/poll/PollQueryServiceTest.java
git commit -m "feat: 여론조사 조회용 엔티티와 리포지토리 추가"
```

## Task 4: overview endpoint TDD

**Files:**
- Create: `services/backend/src/main/java/com/everyones/lawmaking/common/dto/response/election/ElectionPollOverviewResponse.java`
- Create: `services/backend/src/main/java/com/everyones/lawmaking/service/election/poll/PollQueryService.java`
- Modify: `services/backend/src/main/java/com/everyones/lawmaking/controller/ElectionController.java`
- Create: `services/backend/src/test/java/com/everyones/lawmaking/controller/ElectionPollControllerTest.java`
- Modify: `services/backend/src/test/java/com/everyones/lawmaking/service/election/poll/PollQueryServiceTest.java`

- [ ] **Step 1: overview 실패 테스트 작성**

최소 다음을 검증한다.

- `/v1/election/polls/overview?election_id=...&region_code=11` 호출 가능
- 응답에 `leading_party`, `party_trend`, `latest_surveys`가 존재
- 무응답/기타가 `undecided`로 집계

- [ ] **Step 2: 실패 확인**

Run: `cd services/backend && ./gradlew test --tests 'com.everyones.lawmaking.controller.ElectionPollControllerTest' --tests 'com.everyones.lawmaking.service.election.poll.PollQueryServiceTest'`
Expected: FAIL because endpoint/DTO/aggregation do not exist

- [ ] **Step 3: 최소 구현**

overview DTO, service aggregation, controller endpoint를 구현한다.

- [ ] **Step 4: 테스트 재실행**

Run: `cd services/backend && ./gradlew test --tests 'com.everyones.lawmaking.controller.ElectionPollControllerTest' --tests 'com.everyones.lawmaking.service.election.poll.PollQueryServiceTest'`
Expected: PASS for overview cases

- [ ] **Step 5: Commit**

```bash
git add services/backend/src/main/java/com/everyones/lawmaking/common/dto/response/election/ElectionPollOverviewResponse.java \
        services/backend/src/main/java/com/everyones/lawmaking/service/election/poll/PollQueryService.java \
        services/backend/src/main/java/com/everyones/lawmaking/controller/ElectionController.java \
        services/backend/src/test/java/com/everyones/lawmaking/controller/ElectionPollControllerTest.java \
        services/backend/src/test/java/com/everyones/lawmaking/service/election/poll/PollQueryServiceTest.java
git commit -m "feat: 여론조사 전체 탭 API 추가"
```

## Task 5: party / region / candidate endpoint TDD

**Files:**
- Create: `services/backend/src/main/java/com/everyones/lawmaking/common/dto/response/election/ElectionPollPartyResponse.java`
- Create: `services/backend/src/main/java/com/everyones/lawmaking/common/dto/response/election/ElectionPollRegionResponse.java`
- Create: `services/backend/src/main/java/com/everyones/lawmaking/common/dto/response/election/ElectionPollCandidateResponse.java`
- Modify: `services/backend/src/main/java/com/everyones/lawmaking/service/election/poll/PollQueryService.java`
- Modify: `services/backend/src/main/java/com/everyones/lawmaking/controller/ElectionController.java`
- Modify: `services/backend/src/test/java/com/everyones/lawmaking/controller/ElectionPollControllerTest.java`
- Modify: `services/backend/src/test/java/com/everyones/lawmaking/service/election/poll/PollQueryServiceTest.java`

- [ ] **Step 1: party/region/candidate 실패 테스트 작성**

최소 다음을 검증한다.

- `party` 응답에 `trend_series`, `regional_distribution`
- `region` 응답에 `party_snapshot`, `candidate_snapshot`, `latest_surveys`
- `candidate` 응답이 `MATCHUP` 우선, 없으면 `CANDIDATE_FIT` fallback

- [ ] **Step 2: 실패 확인**

Run: `cd services/backend && ./gradlew test --tests 'com.everyones.lawmaking.controller.ElectionPollControllerTest' --tests 'com.everyones.lawmaking.service.election.poll.PollQueryServiceTest'`
Expected: FAIL because extra DTOs and fallback logic are missing

- [ ] **Step 3: 최소 구현**

party/region/candidate DTO와 집계 로직, controller endpoint를 추가한다.

- [ ] **Step 4: 테스트 재실행**

Run: `cd services/backend && ./gradlew test --tests 'com.everyones.lawmaking.controller.ElectionPollControllerTest' --tests 'com.everyones.lawmaking.service.election.poll.PollQueryServiceTest'`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/backend/src/main/java/com/everyones/lawmaking/common/dto/response/election/ElectionPollPartyResponse.java \
        services/backend/src/main/java/com/everyones/lawmaking/common/dto/response/election/ElectionPollRegionResponse.java \
        services/backend/src/main/java/com/everyones/lawmaking/common/dto/response/election/ElectionPollCandidateResponse.java \
        services/backend/src/main/java/com/everyones/lawmaking/service/election/poll/PollQueryService.java \
        services/backend/src/main/java/com/everyones/lawmaking/controller/ElectionController.java \
        services/backend/src/test/java/com/everyones/lawmaking/controller/ElectionPollControllerTest.java \
        services/backend/src/test/java/com/everyones/lawmaking/service/election/poll/PollQueryServiceTest.java
git commit -m "feat: 여론조사 정당 지역 후보 API 추가"
```

## Task 6: 프론트 poll 타입과 query hook TDD

**Files:**
- Modify: `services/web/types/type/election/election.ts`
- Modify: `services/web/app/election/apis/contracts.ts`
- Modify: `services/web/app/election/apis/apis.ts`
- Modify: `services/web/app/election/apis/queries.ts`
- Modify: `services/web/app/election/components/ElectionPollView.test.tsx`

- [ ] **Step 1: 실패 테스트 작성**

`ElectionPollView.test.tsx`에 최소 다음을 추가한다.

- overview query가 없으면 전체 탭 렌더링 실패
- party query 데이터가 들어오면 정당별 탭이 실데이터 label을 렌더링

- [ ] **Step 2: 실패 확인**

Run: `cd services/web && npm test -- app/election/components/ElectionPollView.test.tsx`
Expected: FAIL because poll hooks/types do not exist

- [ ] **Step 3: 최소 구현**

poll 응답 타입, API 함수, query key, hook을 추가한다.

- [ ] **Step 4: 테스트 재실행**

Run: `cd services/web && npm test -- app/election/components/ElectionPollView.test.tsx`
Expected: PASS for API wiring mocks

- [ ] **Step 5: Commit**

```bash
git add services/web/types/type/election/election.ts \
        services/web/app/election/apis/contracts.ts \
        services/web/app/election/apis/apis.ts \
        services/web/app/election/apis/queries.ts \
        services/web/app/election/components/ElectionPollView.test.tsx
git commit -m "feat: 여론조사 프론트 타입과 쿼리 훅 추가"
```

## Task 7: ElectionMapShell 상태 승격과 전체/정당별/지역별 뷰 연동

**Files:**
- Modify: `services/web/app/election/components/ElectionMapShell.tsx`
- Modify: `services/web/app/election/components/ElectionPollView.tsx`
- Modify: `services/web/app/election/components/PollRegionPanel.tsx`
- Modify: `services/web/app/election/components/ElectionPollView.test.tsx`

- [ ] **Step 1: 실패 테스트 작성**

다음 시나리오를 테스트에 반영한다.

- `selectedElectionId`가 바뀌면 poll query 인자가 바뀐다
- 전체 탭이 overview 실데이터를 렌더링한다
- 지역별 탭이 region 응답 기반 패널을 렌더링한다

- [ ] **Step 2: 실패 확인**

Run: `cd services/web && npm test -- app/election/components/ElectionPollView.test.tsx`
Expected: FAIL because shell state and real-data mapping are incomplete

- [ ] **Step 3: 최소 구현**

- `ElectionMapShell`에 `selectedElectionId` 공통 상태 승격
- `ElectionPollView`에서 목업 import 제거
- `PollRegionPanel`을 region endpoint 기반으로 교체

- [ ] **Step 4: 테스트 재실행**

Run: `cd services/web && npm test -- app/election/components/ElectionPollView.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/web/app/election/components/ElectionMapShell.tsx \
        services/web/app/election/components/ElectionPollView.tsx \
        services/web/app/election/components/PollRegionPanel.tsx \
        services/web/app/election/components/ElectionPollView.test.tsx
git commit -m "feat: 여론조사 전체 정당 지역 탭 실데이터 연동"
```

## Task 8: 후보자별 탭 실데이터 연동 TDD

**Files:**
- Create: `services/web/app/election/components/ElectionCandidatePollPanel.tsx`
- Create: `services/web/app/election/components/ElectionCandidatePollPanel.test.tsx`
- Modify: `services/web/app/election/components/ElectionPollView.tsx`
- Modify: `services/web/app/election/components/ElectionPollView.test.tsx`

- [ ] **Step 1: 실패 테스트 작성**

최소 다음을 검증한다.

- candidate query가 `MATCHUP`이면 그 데이터를 우선 렌더링
- candidate query가 `CANDIDATE_FIT`만 있어도 fallback 렌더링
- 지역 선택 후 후보 목록이 표시되고 기본 후보가 선택된다

- [ ] **Step 2: 실패 확인**

Run: `cd services/web && npm test -- app/election/components/ElectionCandidatePollPanel.test.tsx app/election/components/ElectionPollView.test.tsx`
Expected: FAIL because candidate panel and fallback logic do not exist

- [ ] **Step 3: 최소 구현**

후보자별 패널 컴포넌트를 분리하고, `ElectionPollView`에서 `candidate` endpoint 응답을 연결한다.

- [ ] **Step 4: 테스트 재실행**

Run: `cd services/web && npm test -- app/election/components/ElectionCandidatePollPanel.test.tsx app/election/components/ElectionPollView.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/web/app/election/components/ElectionCandidatePollPanel.tsx \
        services/web/app/election/components/ElectionCandidatePollPanel.test.tsx \
        services/web/app/election/components/ElectionPollView.tsx \
        services/web/app/election/components/ElectionPollView.test.tsx
git commit -m "feat: 여론조사 후보자별 탭 실데이터 연동"
```

## Task 9: 최종 검증과 마감

**Files:**
- Modify if needed: `docs/superpowers/specs/2026-04-11-election-poll-real-data-design.md`

- [ ] **Step 1: 백엔드 테스트 전체 실행**

Run: `cd services/backend && ./gradlew test`
Expected: PASS

- [ ] **Step 2: 프론트 테스트 실행**

Run: `cd services/web && npm test -- app/election/components/ElectionPollView.test.tsx app/election/components/ElectionCandidatePollPanel.test.tsx`
Expected: PASS

- [ ] **Step 3: 프론트 lint 실행**

Run: `cd services/web && npm run lint`
Expected: PASS

- [ ] **Step 4: 수동 점검**

Run: `cd services/web && npm run dev`
Expected: 선거-여론조사 탭에서 전체/정당별/지역별/후보자별이 실제 응답 기준으로 렌더링되고, 데이터 없는 조합은 빈 상태를 노출

- [ ] **Step 5: 설계 문서와 구현 차이 반영**

구현 중 달라진 endpoint shape 또는 fallback 규칙이 있으면 설계 문서에 최소 수정만 반영한다.

- [ ] **Step 6: 최종 커밋**

```bash
git add services/backend services/web docs/superpowers/specs/2026-04-11-election-poll-real-data-design.md
git commit -m "feat: 선거 여론조사 탭 실데이터 연동"
```
