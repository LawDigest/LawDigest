# 법안 리포트와 툴팁 단계 분리 설계

## 목표

법안 리포트 생성과 법률용어 툴팁 보강을 서로 독립된 실행 과정으로 분리한다. 리포트가 품질 검증을 통과하면 툴팁 처리 결과와 무관하게 즉시 파일과 DB에 반영하고, 툴팁 실패는 별도 manifest에만 기록한다.

## 실행 경계

### 1. 리포트 생성

`bill-agent-report`는 법안과 공식 근거를 읽어 `report_body`만 생성한다.

- 법률용어 후보를 조회하거나 evidence에 넣지 않는다.
- 에이전트 출력은 `report_body`만 포함한다.
- 기존 Markdown 구조, 문체, 제목, 내부 표현 검증을 통과한 결과만 성공으로 본다.
- 성공한 각 법안은 배치의 다른 법안이나 후속 툴팁 처리와 무관하게 즉시 DB에 반영한다.
- 생성 manifest는 성공 법안 ID와 저장 경로를 후속 단계에 전달할 수 있어야 한다.

### 2. 툴팁 보강

`bill-agent-tooltip`은 이미 저장된 리포트를 입력으로 받는다.

- 기본 입력은 리포트 생성 manifest의 성공 항목이다.
- 필요하면 DB에서 툴팁이 없는 리포트를 직접 조회할 수 있다.
- 리포트 본문에서 용어 후보를 찾고 로컬 법률용어 사전과 법제처 fallback을 조회한다.
- 에이전트는 리포트를 다시 쓰지 않고 후보별 `confidence`와 `relevance`만 판정한다.
- 코드 게이트는 후보 term/aliases와 surface의 정규화 일치, `confidence=high`, `relevance=high`를 모두 요구한다.
- 최종 정의는 에이전트가 작성한 문자열이 아니라 사전 후보 정의를 사용한다.
- 후보가 없거나 승인 후보가 없으면 정상적인 `skipped` 결과로 기록한다.

## 데이터 흐름

```text
Bill.summary + 공식 근거
  -> bill-agent-report
  -> Markdown 검증
  -> 파일 저장 + Bill.gpt_summary 즉시 반영
  -> report manifest

report manifest 또는 저장된 Bill.gpt_summary
  -> bill-agent-tooltip
  -> 법률용어 후보 조회
  -> 에이전트 문맥 적합성 판정
  -> 코드 게이트
  -> 툴팁 적용본 검증
  -> 파일 저장 + Bill.gpt_summary 재반영
  -> tooltip manifest
```

## 실패 처리

- 리포트 생성 실패는 기존 재시도 분류와 항목별 즉시 반영 계약을 유지한다.
- 툴팁 실행 실패는 리포트 생성 성공을 취소하지 않는다.
- 툴팁 적용 전 원문은 메모리에서 보존하고, 파싱·판정·검증 중 하나라도 실패하면 DB를 갱신하지 않는다.
- 툴팁을 제거한 적용 결과가 원문과 같지 않으면 본문 변조로 보고 실패 처리한다.
- 툴팁 manifest는 `success`, `skipped`, `failed`, 실패 유형, 재시도 횟수, DB 반영 여부를 항목별로 기록한다.

## 운영 인터페이스

- 기존 `bill-agent-report` 명령은 리포트 생성만 수행한다.
- 새 `bill-agent-tooltip` 명령은 `--source-manifest`, `--target missing|all`, `--limit`, `--concurrency`, `--batch-session-size`, `--failure-retry-attempts`, `--inspection`을 지원한다.
- `--source-manifest`가 있으면 manifest의 성공 법안만 처리한다.
- `dry_run`은 결과 파일과 manifest만 만들고 DB를 갱신하지 않는다.

## 검증 기준

- 리포트 프롬프트와 evidence에 법률용어 후보 또는 정의가 없어야 한다.
- 리포트 생성 성공 건은 툴팁 실행 없이 DB에 반영돼야 한다.
- 툴팁 실패 시 기존 `gpt_summary`가 유지돼야 한다.
- 알려진 변리사법 오탐 정의는 툴팁 단계에서 거부돼야 한다.
- 정상 후보는 별도 단계에서만 주입되고, 툴팁을 제거한 본문은 입력 본문과 같아야 한다.

## 비범위

- 법제처 사전의 복수 의미 스키마 개편은 이번 변경에 포함하지 않는다.
- 웹 툴팁 렌더러와 `{{term:definition}}` 표시 계약은 변경하지 않는다.
- 리포트 본문 구조와 기존 DB 요약 필드 계약은 변경하지 않는다.
