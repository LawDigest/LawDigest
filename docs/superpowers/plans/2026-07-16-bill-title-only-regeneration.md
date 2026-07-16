# 법안 제목 전용 재생성 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 원문 요약이 제목으로 복사된 법안 중 지정한 수만큼을 골라 기존 리포트는 보존하고 에이전트가 제목만 재생성한다.

**Architecture:** 새 `bill_title_regeneration.py`에 대상 판정, 제목 전용 프롬프트·파서·실행기를 모으고 기존 `agentic_bill_report.py`의 Codex 실행 환경과 제목 검증기를 재사용한다. DB 저장은 `db.py`의 제목 전용 조건부 UPDATE로 분리하며 데이터 런타임에는 명시적인 `bill-title-regenerate` 명령을 연결한다.

**Tech Stack:** Python 3.13, PyMySQL, argparse, pytest, Codex CLI

---

### Task 1: 제목 전용 조건부 저장

**Files:**
- Modify: `services/ai/src/lawdigest_ai/db.py:90-119`
- Test: `services/ai/tests/test_db.py`

- [ ] 조회 당시 제목이 같은 경우 `title`만 UPDATE하는 실패 테스트를 작성한다.
- [ ] `uv run pytest tests/test_db.py -q`를 실행해 새 함수 부재로 실패하는지 확인한다.
- [ ] `update_bill_title_if_current(bill_id, title, expected_title, mode)`를 최소 구현하고 row count를 반환한다.
- [ ] 테스트를 다시 실행해 `gpt_summary`가 SQL에 포함되지 않고 조건부 UPDATE가 통과하는지 확인한다.

### Task 2: 3,539건 대상 판정과 조회

**Files:**
- Create: `services/ai/src/lawdigest_ai/processor/bill_title_regeneration.py`
- Create: `services/ai/tests/processor/test_bill_title_regeneration.py`

- [ ] 공백·머리말·말줄임표 정규화 후 raw summary prefix를 판정하는 테스트를 작성한다.
- [ ] 에이전트형 Markdown 조건과 정렬·limit을 적용하는 조회 테스트를 작성한다.
- [ ] 대상 판정 helper와 `_fetch_bill_title_regeneration_targets`를 최소 구현한다.
- [ ] 관련 테스트가 통과하는지 확인한다.

### Task 3: 제목 전용 에이전트 생성과 검증

**Files:**
- Modify: `services/ai/src/lawdigest_ai/processor/bill_title_regeneration.py`
- Test: `services/ai/tests/processor/test_bill_title_regeneration.py`

- [ ] 프롬프트가 제목만 요구하고 기존 `summary`, `gpt_summary`, 정확한 `bill_name`을 제공하는 테스트를 작성한다.
- [ ] JSON 파서가 순서와 `bill_id` 일치, 중복·누락, 기존 제목 복사를 거부하고 `_validate_generated_title`을 적용하는 테스트를 작성한다.
- [ ] 한 번의 Codex 호출로 최대 5건의 제목을 생성하는 메서드를 최소 구현한다.
- [ ] 관련 테스트를 실행해 통과시킨다.

### Task 4: 실행 서비스와 CLI 연결

**Files:**
- Modify: `services/ai/src/lawdigest_ai/processor/bill_title_regeneration.py`
- Modify: `services/data/src/lawdigest_data/runtime/pipeline.py:620-746`
- Modify: `services/data/src/lawdigest_data/runtime/cli.py:42-245`
- Test: `services/ai/tests/processor/test_bill_title_regeneration.py`
- Test: `services/data/tests/test_pipeline_runtime.py`

- [ ] `dry_run`에서 저장하지 않고 `prod`에서 성공한 제목만 조건부 저장하는 실행 테스트를 작성한다.
- [ ] `bill-title-regenerate --mode --limit --output-dir --codex-model` CLI 전달 테스트를 작성한다.
- [ ] `run_agentic_bill_title_regeneration`과 런타임 메서드·CLI를 최소 구현한다.
- [ ] AI 및 데이터 런타임 관련 테스트를 실행해 통과시킨다.

### Task 5: 문서화와 정적 검증

**Files:**
- Modify: `docs/ai/bill-report-agent-pipeline.md`

- [ ] 제목 전용 대상 조건, dry-run, 운영 명령, title-only 저장 계약을 문서화한다.
- [ ] `ruff check src tests`와 관련 pytest를 실행한다.
- [ ] `git diff --check`와 변경 범위를 확인한다.

### Task 6: 운영 5건 선행 실행

**Files:**
- Runtime artifact: `/tmp/lawdigest-bill-title-regeneration-<timestamp>/result.json`

- [ ] 운영 DB를 읽는 dry-run에서 대상이 정확히 5건인지 확인한다.
- [ ] 생성된 제목 5건이 현재 제목 계약을 통과하는지 검토한다.
- [ ] `prod`로 같은 대상 5건의 `title`만 조건부 업데이트한다.
- [ ] 실행 전후 `gpt_summary` SHA-256과 새 제목을 조회해 보존·반영을 검증한다.
- [ ] 결과와 실패 여부를 사용자에게 보고한다.
