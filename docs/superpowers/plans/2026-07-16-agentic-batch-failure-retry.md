# Agentic Batch Failure Retry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan.

**Goal:** 배치 세션에서 실패한 법안 리포트 항목만 새 단일 세션으로 자동 재시도하고, 최종 manifest와 DB 반영 결과가 재시도 이후 상태를 정확히 나타내게 한다.

**Architecture:** 기존 배치 생성은 그대로 유지하되 실패 결과에 안정적인 `failure_type`을 부여한다. 모든 최초 생성이 끝난 뒤 `run_agentic_bill_reports`가 재시도 가능한 배치 실패만 골라 `write_report` 기반의 새 단일 세션으로 순차 재시도한다. 실패 이력과 사용량은 항목의 `retry.history`에 보존하며, 최종 통계와 `stop_on_error` 판단은 재시도 완료 후 계산한다.

**Tech Stack:** Python 3.12, pytest, Typer/argparse 기반 runtime CLI, uv, GitHub CLI

---

### Task 1: 배치 실패 분류와 자동 재시도 동작을 테스트로 고정

**Files:**
- Modify: `services/ai/tests/processor/test_agentic_bill_report.py`

- [ ] 배치의 한 항목이 `empty_output`으로 실패한 뒤 새 단일 세션에서 성공하는 테스트를 추가한다. `title` structured output을 사용하고, 호출 횟수 3회, DB 저장 2건, 최종 성공 2건, `retried_item_count=1`, `retry_success_count=1`, `retry.attempt_count=1`, 초기 실패 이력을 검증한다.
- [ ] `failure_retry_attempts=0`이면 재시도하지 않는 테스트를 추가한다.
- [ ] 음수 `failure_retry_attempts`를 거부하는 테스트를 추가한다.
- [ ] 재시도 후에도 실패하고 `stop_on_error=True`이면 재시도를 모두 수행한 다음 오류를 내는 테스트를 추가한다.
- [ ] `persistence_error`는 재시도하지 않는 테스트를 추가한다.
- [ ] 복수 재시도의 `attempt` 번호와 실패 이력 사용량 합산을 검증하고, 한 항목의 재시도 예외가 다른 실패 항목의 재시도를 막지 않는 테스트를 추가한다.
- [ ] 실행 전 입력·설정 오류는 재시도하지 않고, 기존 0-byte 출력은 `empty_output`으로 분류하며, 재시도 생성 성공 뒤 persistence 실패는 `persistence_error`로 종료되는 테스트를 추가한다.
- [ ] 다음 명령으로 RED를 확인한다. 실패 원인은 새 인자/통계/분류가 아직 없기 때문이어야 한다.
  - Run: `cd services/ai && uv run --frozen pytest tests/processor/test_agentic_bill_report.py -q`

### Task 2: 실패 분류와 재시도 오케스트레이션 구현

**Files:**
- Modify: `services/ai/src/lawdigest_ai/processor/agentic_bill_report.py`

- [ ] `DEFAULT_FAILURE_RETRY_ATTEMPTS = 1`과 재시도 가능한 실패 유형 집합(`empty_output`, `execution_error`, `invalid_output`)을 정의한다.
- [ ] `BillReportGenerationError`와 `write_report`에 구조화된 `failure_type` 계약을 추가한다. 세션/프로세스 실패는 `execution_error`, 없거나 0-byte인 출력은 `empty_output`, JSON·제목·본문 검증 실패는 `invalid_output`으로 분류해 단일 재시도 실패도 문자열 파싱 없이 이력을 남길 수 있게 한다.
- [ ] `write_reports_batch`에도 같은 실패 분류를 적용하고, 성공 콜백(DB 저장) 실패만 `persistence_error`로 분리한다. 배치 호출 바깥의 예외는 발생 단계가 보존되도록 구조화한다.
- [ ] 배치 바깥에서 발생한 입력 검증·설정·evidence 준비 오류는 별도 비재시도 실패(`configuration_error`)로 보존하고, 실제 subprocess/session 실행 경계의 예외만 `execution_error`로 분류한다.
- [ ] `run_agentic_bill_reports`에 `failure_retry_attempts` 인자를 추가하고 0 이상의 정수만 허용한다.
- [ ] 최초 배치 작업이 모두 끝난 뒤 재시도 가능한 실패 항목만 새 단일 세션으로 재생성한다. 초기 실패는 `attempt: 0`, 각 실패한 재시도는 해당 재시도 번호로 `retry.history`에 기록하고, 실제 시도한 횟수를 `retry.attempt_count`에 저장한다.
- [ ] 성공한 재시도 결과가 원래 항목을 대체하되 `retry` 메타데이터를 유지하고 DB 성공 콜백은 성공 시 정확히 한 번 호출되게 한다. 재시도 생성 뒤 단일 persistence가 실패하면 `persistence_error` 최종 항목으로 바꾸고 모델을 다시 호출하지 않는다.
- [ ] `stop_on_error` 판단을 재시도 완료 뒤로 옮긴다. 단일/레거시 경로의 기존 의미는 유지한다.
- [ ] 최종 manifest에 `retried_item_count`, `retry_success_count`를 추가하고 `retry.history[*].usage`도 전체 usage 합계에 포함한다.
- [ ] 기존 직접 제목 생성, 제목 검증, DB `title` 저장 경로를 변경하지 않는다.
- [ ] Task 1 테스트를 다시 실행해 GREEN을 확인한다.
  - Run: `cd services/ai && uv run --frozen pytest tests/processor/test_agentic_bill_report.py -q`
- [ ] 구현과 테스트를 커밋한다.
  - Commit: `fix: 배치 실패 항목 자동 재시도 추가`

### Task 3: 데이터 파이프라인과 CLI 계약 연결

**Files:**
- Modify: `services/data/tests/test_pipeline_runtime.py`
- Modify: `services/data/src/lawdigest_data/runtime/cli.py`
- Modify: `services/data/src/lawdigest_data/runtime/pipeline.py`

- [ ] runtime/CLI 테스트에 기본값 1과 명시값 0 또는 2가 AI 리포트 실행 함수까지 전달되는 사례를 추가한다.
- [ ] 다음 명령으로 RED를 확인한다. 새 CLI 옵션과 pass-through 인자가 없어서 실패해야 한다.
  - Run: `cd services/data && uv run --frozen pytest tests/test_pipeline_runtime.py -q`
- [ ] 공통 AI summary 인자와 `bill-agent-report` 명령에 `--failure-retry-attempts`를 추가한다.
- [ ] `run_ai_summary`, `_run_agentic_bill_report`, `run_bill_agent_report`가 값을 그대로 전달하게 한다.
- [ ] runtime 테스트를 다시 실행해 GREEN을 확인한다.
  - Run: `cd services/data && uv run --frozen pytest tests/test_pipeline_runtime.py -q`
- [ ] 변경을 커밋한다.
  - Commit: `feat: 배치 재시도 설정을 데이터 파이프라인에 연결`

### Task 4: 운영 문서와 출력 QA 후속 이슈 정리

**Files:**
- Modify: `docs/ai/bill-report-agent-pipeline.md`

- [ ] 문서에 기본 1회 자동 재시도, 0으로 비활성화, 재시도 대상/비대상, manifest 통계와 이력 필드를 설명한다.
- [ ] 출력 QA 테스트나 구현은 브랜치에 추가하지 않았는지 `git diff --check`와 테스트 파일 검색으로 확인한다.
- [ ] GitHub Task 이슈 템플릿을 사용해 출력 QA 문제를 한글 제목/본문으로 등록한다. 범위는 품질 판정 기준, manifest 표현, 배치·즉시·복구 경로의 회귀 테스트이며 이번 PR에는 포함하지 않는다고 명시한다.
- [ ] 문서 변경을 커밋한다.
  - Commit: `docs: 배치 실패 재시도 동작 문서화`

### Task 5: 전체 검증, 푸시, 인계

**Files:**
- Verify only

- [ ] AI 전체 테스트를 새로 실행한다.
  - Run: `cd services/ai && uv run --frozen pytest -q`
- [ ] 데이터 서비스 전체 테스트를 새로 실행한다.
  - Run: `cd services/data && uv run --frozen pytest -q`
- [ ] 저장소의 실제 lint 명령을 설정 파일/CI에서 확인한 뒤 AI와 data 변경 범위에 실행한다.
- [ ] `git diff --check`, `git status --short`, `git log --oneline origin/main..HEAD`로 변경과 커밋 범위를 확인한다.
- [ ] `superpowers:verification-before-completion` 기준으로 최신 검증 결과를 확인한다.
- [ ] 브랜치 `fix/agentic-batch-retry/codex`를 원격에 push한다.
- [ ] 완료 보고에 테스트·lint 결과, 출력 QA 이슈 URL, 제목 생성 경로가 유지됐다는 근거, 후속 작업 5개를 포함하고 PR 생성 여부를 묻는다.
