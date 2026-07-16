# 에이전틱 법안 리포트 실패 항목 자동 재시도 설계

## 배경

에이전틱 법안 리포트는 여러 법안을 한 Codex 세션에서 순서대로 처리할 수 있다. 세션의 한 turn이 빈 출력을 남기거나 실행·검증에 실패하면 해당 법안만 실패하지만, 현재 runner는 실패 항목을 그대로 manifest에 기록하고 종료한다. 정상 처리된 법안까지 다시 실행하지 않으면서 실패한 법안만 복구할 수 있는 자동 재시도가 필요하다.

출력 QA 집계는 이번 구현에 포함하지 않는다. 잔여 JSON wrapper나 별도 품질 문제를 manifest에 모으는 기능은 GitHub 이슈로 남긴다.

## 목표

- 배치 세션에서 생성에 실패한 법안만 새 단건 Codex 세션으로 재시도한다.
- 기본 재시도 횟수는 1회이며, 0으로 끌 수 있다.
- 재시도 후 최종 결과와 이력을 manifest에서 확인할 수 있게 한다.
- 재시도 성공 항목은 DB에 한 번만 반영한다.
- `stop_on_error`는 재시도를 모두 소진한 뒤에도 실패가 남았을 때 적용한다.

## 범위 밖

- 이미 성공한 법안 재생성
- DB 저장 실패를 해결하기 위한 모델 재호출
- 지수 백오프, circuit breaker, provider 전환
- 출력 QA issue 집계 및 자동 판정
- 기존 title 생성·검증 계약 변경

## 선택한 접근

초기 배치 실행이 끝난 뒤 실패 항목을 모아 새 단건 세션으로 다시 실행한다. 배치 세션을 재개하지 않는 이유는 실패 turn의 세션 상태가 다음 시도에 영향을 주지 않게 하기 위해서다. 성공 항목은 건드리지 않는다.

재시도는 `failure_retry_attempts`로 제어한다. 허용 범위는 0~3회이며 기본값은 1회다. CLI에는 `--failure-retry-attempts`를 노출한다.

## 실패 분류

재시도 대상은 배치 처리 중 발생한 생성 실패다.

- `empty_output`: 결과 파일이 없거나 비어 있음
- `execution_error`: Codex subprocess가 실패하거나 세션을 재개할 수 없음
- `invalid_output`: JSON 파싱, title 계약, Markdown 품질 검증 실패

DB upsert 과정의 실패는 `persistence_error`로 구분하고 모델을 다시 호출하지 않는다. 입력 검증처럼 실행 전에 발생하는 설정 오류도 재시도하지 않는다.

분류는 사용자 메시지용 문자열만 다시 해석하지 않는다. 실패를 만드는 경계에서 `failure_type`을 status item에 기록하고 runner는 이 값을 보고 재시도 여부를 결정한다.

## 처리 흐름

1. 기존 방식으로 단건 또는 배치 세션을 실행한다.
2. 모든 초기 배치가 끝난 뒤 `batch_index`가 있고 `status == "failed"`인 항목을 고른다.
3. 재시도 가능한 `failure_type`이면 해당 법안을 새 단건 세션으로 실행한다.
4. 성공하면 원래 위치의 실패 항목을 성공 항목으로 교체한다.
5. 실패하면 제한 횟수까지 새 단건 세션으로 다시 실행한다.
6. 각 시도의 원래 실패 정보는 `retry.history`에 남긴다.
7. 재시도를 마친 뒤 `stop_on_error`를 평가한다.
8. 최종 items와 통계를 `manifest.json`에 기록한다.

단건 모드에서 처음부터 실행한 항목은 이번 자동 재시도 대상이 아니다. 이 변경은 배치 세션의 부분 실패 복구만 다룬다.

## manifest 계약

재시도된 항목에는 다음 정보를 추가한다.

```json
{
  "retry": {
    "attempt_count": 1,
    "history": [
      {
        "attempt": 1,
        "failure_type": "empty_output",
        "error": "Codex agent report body is empty."
      }
    ]
  }
}
```

전체 통계에는 다음 값을 추가한다.

- `retried_item_count`: 한 번 이상 재시도한 법안 수
- `retry_success_count`: 재시도 후 성공한 법안 수

기존 `success_count`, `failure_count`, `db_upserted_count`는 재시도가 끝난 최종 항목을 기준으로 계산한다. 재시도 호출의 token usage도 기존 usage 합산 규칙에 포함한다.

## 오류 처리

- `failure_retry_attempts`가 0보다 작거나 3보다 크면 실행 전에 `ValueError`를 발생시킨다.
- 재시도 중 예외가 발생해도 다른 재시도 항목은 계속 처리한다. `stop_on_error`는 최종 실패가 남았을 때만 실행 전체를 실패시킨다.
- DB 저장이 성공한 항목은 다시 저장하지 않는다.
- 재시도 불가능한 실패는 기존 항목을 유지하고 이력을 만들지 않는다.

## 변경 지점

- `services/ai/src/lawdigest_ai/processor/agentic_bill_report.py`
  - 실패 유형 기록
  - 배치 실패 항목 선별 및 단건 재시도
  - retry metadata와 통계 추가
- `services/data/src/lawdigest_data/runtime/pipeline.py`
  - `failure_retry_attempts` 전달
- `services/data/src/lawdigest_data/runtime/cli.py`
  - `--failure-retry-attempts` 옵션 추가
- `services/ai/tests/processor/test_agentic_bill_report.py`
  - 빈 출력 재시도 성공, 재시도 소진, 재시도 비활성화 검증
- `services/data/tests/test_pipeline_runtime.py`
  - runtime 전달 계약 검증
- 관련 AI 파이프라인 문서
  - 운영 옵션과 manifest 필드 설명

## 검증

- 기존 에이전틱 리포트 테스트가 모두 통과해야 한다.
- 새 테스트는 구현 전 실패하고 구현 후 통과해야 한다.
- `failure_retry_attempts=1`에서 빈 출력 항목만 단건 재시도되는지 확인한다.
- 재시도 성공 항목이 DB에 정확히 한 번 저장되는지 확인한다.
- `failure_retry_attempts=0`에서 기존 동작이 유지되는지 확인한다.
- CLI와 runtime이 값을 누락 없이 전달하는지 확인한다.
- AI 및 data lint를 실행한다.

