# 법안 상태 동기화 파이프라인 lifecycle·vote 재구성 설계

> 작성일: 2026-04-16
> 관련 이슈: #61, #62, #63
> 기준 레퍼런스: `references/assembly-api-mcp`

---

## 1. 배경

PR #64에서 법안 본체 적재 파이프라인은 `후보 발견 -> hydrate -> DB upsert` 구조로 정리되었다. 반면 `bill_status_sync_dag`는 여전히 `timeline`, `result`, `vote`를 테이블 중심으로 분리한 예전 구조를 유지하고 있다.

이 구조의 한계는 다음과 같다.

1. `timeline`과 `result`가 같은 법안 lifecycle의 다른 표면인데도 별도 파이프라인으로 흩어져 있다.
2. 실패 복구 단위가 테이블 기준이라 상태 일관성이 약하다.
3. checkpoint와 artifact 전략이 본체 적재 파이프라인만큼 명확하지 않다.
4. `DataFetcher`와 `WorkFlowManager`에 상태 해석 책임이 과도하게 집중되어 있다.

---

## 2. 레퍼런스 채택 기준

`assembly-api-mcp`에서 LawDigest가 채택하는 패턴은 다음과 같다.

1. endpoint가 아니라 capability 기준으로 파이프라인을 나눈다.
2. `BILL_ID -> BILL_NO -> lifecycle / summary / proposers`처럼 역할별 보강 순서를 분리한다.
3. discovery 와 hydrate 를 분리하고, partial failure를 전체 실패로 전파하지 않는다.
4. raw source 와 DB projection 사이에 정규화 계층을 둔다.

이번 리팩토링에서는 이 원칙을 상태 동기화에 맞게 `lifecycle + vote` capability 로 적용한다.

---

## 3. 최종 아키텍처

### 3.1 capability

#### LawmakerSync
- 의원/정당 기준 데이터를 먼저 동기화한다.
- downstream lifecycle/vote 적재가 참조하는 master data를 안정화한다.

#### BillLifecycleSync
- `BillTimeline` 적재
- `Bill.stage`, `Bill.bill_result`, `Bill.committee` 최신 상태 projection 갱신
- source of truth는 `ALLBILL`이고, `BILLJUDGE`는 누락 필드 보강용 보조 source 로만 사용한다.

#### BillVoteSync
- `VoteRecord`
- `VoteParty`
- 표결 source 는 lifecycle 과 별도 capability 로 운영한다.

### 3.2 DAG 흐름

```text
update_lawmakers
  -> fetch_lifecycle -> upsert_lifecycle
  -> fetch_vote -> upsert_vote
```

- `fetch_*`는 raw artifact만 저장한다.
- `upsert_*`가 성공했을 때만 checkpoint를 전진시킨다.
- lifecycle 과 vote 는 서로 독립적으로 재실행 가능하다.

---

## 4. 데이터 흐름

### 4.1 lifecycle

1. `LifecycleStatusFetcher`가 `ALLBILL` snapshot을 수집한다.
2. 위원회/심사 필드가 비어 있는 법안만 `BILLJUDGE`로 보강한다.
3. `BillLifecycleProjector`가 raw row를 lifecycle event 목록으로 정규화한다.
4. event는 `BillTimeline`에 적재하고, 최신 값은 `Bill` projection으로 반영한다.

생성되는 내부 표준 row:
- `bill_id`
- `stage`
- `committee`
- `status_update_date`
- `bill_result`
- `source_name`
- `source_reference_date`

### 4.2 vote

1. `VoteStatusFetcher`가 본회의 표결 raw data 를 수집한다.
2. 정당별 표결 데이터도 같은 capability 안에서 확보한다.
3. `BillVoteProjector`가 `VoteRecord`, `VoteParty`용 normalized row로 변환한다.
4. 하나의 upsert step 에서 두 projection을 반영한다.

---

## 5. checkpoint 및 failure handling

checkpoint key:
- `bill_status_lifecycle`
- `bill_status_vote`

정책:
1. `fetch` 성공만으로 checkpoint를 전진시키지 않는다.
2. `upsert`가 끝나야 checkpoint를 갱신한다.
3. `dry_run`은 artifact를 남기되 checkpoint를 갱신하지 않는다.
4. bill 단위 결측이나 보강 실패는 warning으로 남기고 batch 전체 실패로 승격하지 않는다.

---

## 6. 구현 원칙

1. `WorkFlowManager`는 orchestration 중심으로 유지한다.
2. 상태 해석은 `status/` 모듈로 분리한다.
3. 기존 `update_bills_timeline`, `update_bills_result`, `update_bills_vote`는 compatibility shim 또는 deprecated wrapper로 유지한다.
4. DAG ID는 유지하고 task graph만 capability 기준으로 재구성한다.

---

## 7. 후속 작업 연결

- `#61`: lifecycle·vote capability 기준 상태 동기화 구현
- `#62`: 발의자 수집 성능 최적화
- `#63`: ingest 품질 모니터링과 점검 쿼리 추가
