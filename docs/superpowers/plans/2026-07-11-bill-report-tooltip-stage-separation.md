# Bill Report Tooltip Stage Separation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 리포트 생성과 법률용어 툴팁 보강을 독립 실행·독립 실패·독립 재시도 가능한 두 과정으로 분리한다.

**Architecture:** 기존 리포트 실행기는 법률용어 evidence와 툴팁 structured output을 제거하고 `report_body`만 생성·검증·즉시 저장한다. 새 `agentic_bill_tooltip.py` 실행기는 생성 manifest 또는 저장된 리포트를 읽어 후보를 만들고, 별도 Codex 판정과 코드 게이트를 거쳐 성공한 경우에만 툴팁 적용본을 다시 저장한다.

**Tech Stack:** Python 3.11+, pytest, Codex CLI JSON events, MySQL `Bill`/`LegalTermDictionary`, argparse runtime CLI

---

### Task 1: 리포트 생성 계약에서 툴팁 제거

**Files:**
- Modify: `services/ai/src/lawdigest_ai/processor/agentic_bill_report.py`
- Test: `services/ai/tests/processor/test_agentic_bill_report.py`

- [ ] 리포트 evidence에 `legal_terms`가 생성되지 않는 실패 테스트를 작성한다.
- [ ] 단건 프롬프트가 `report_body`만 요구하고 후보 정의를 포함하지 않는 실패 테스트를 작성한다.
- [ ] 생성 결과에 tooltips가 있어도 무시하고 깨끗한 report body만 저장하는 실패 테스트를 작성한다.
- [ ] 위 테스트가 기존 코드에서 의도한 이유로 실패하는지 확인한다.
- [ ] `build_bill_report_evidence()`와 `build_bill_report_prompt()`에서 법률용어 후보 결합을 제거한다.
- [ ] 단건·배치 후처리를 report body unwrap, cheap repair, Markdown 검증까지만 수행하도록 바꾼다.
- [ ] 리포트 manifest의 tooltip 통계 의존을 제거한다.
- [ ] 관련 테스트를 실행해 통과를 확인한다.

### Task 2: 독립 툴팁 도메인과 실행기 추가

**Files:**
- Create: `services/ai/src/lawdigest_ai/processor/agentic_bill_tooltip.py`
- Test: `services/ai/tests/processor/test_agentic_bill_tooltip.py`

- [ ] 저장된 리포트와 후보만 포함하는 툴팁 판정 프롬프트 테스트를 작성한다.
- [ ] `confidence=high`, `relevance=high`, exact surface인 후보만 적용하는 테스트를 작성한다.
- [ ] 툴팁 제거 후 원문이 달라지면 실패하고 DB를 갱신하지 않는 테스트를 작성한다.
- [ ] 후보 없음과 승인 후보 없음이 `skipped`로 끝나는 테스트를 작성한다.
- [ ] source manifest의 성공 법안만 대상으로 읽는 테스트를 작성한다.
- [ ] 항목별 성공 직후 DB 반영과 실패 원문 보존 테스트를 작성한다.
- [ ] 위 테스트가 구현 부재로 실패하는지 확인한다.
- [ ] 후보 조회, structured decision 파싱, 코드 게이트, 적용·검증, manifest 기록을 최소 구현한다.
- [ ] 단건 및 세션당 최대 5건 순차 턴, 세션 병렬 실행, 재시도를 구현한다.
- [ ] 새 테스트 전체를 실행해 통과를 확인한다.

### Task 3: 런타임과 CLI에 독립 명령 연결

**Files:**
- Modify: `services/data/src/lawdigest_data/runtime/pipeline.py`
- Modify: `services/data/src/lawdigest_data/runtime/cli.py`
- Test: `services/data/tests/test_pipeline_runtime.py`

- [ ] `PipelineRuntime.run_bill_agent_tooltip()` 위임 테스트를 작성한다.
- [ ] `bill-agent-tooltip` CLI 인자 전달 테스트를 작성한다.
- [ ] 위 테스트가 메서드·명령 부재로 실패하는지 확인한다.
- [ ] 런타임 메서드와 CLI parser/dispatch를 구현한다.
- [ ] 대상이 있으나 성공·skip이 모두 0일 때만 런타임 실패로 처리한다.
- [ ] 데이터 런타임 테스트를 실행해 통과를 확인한다.

### Task 4: 운영 문서와 Cluedoc 갱신

**Files:**
- Modify: `docs/ai/bill-report-agent-pipeline.md`
- Modify: `docs/ai/bill-report-agent-prompt-contract.md`
- Modify: `.cluedoc/ai-intelligence/agentic-bill-report/README.md`

- [ ] 전체 흐름을 리포트 생성과 툴팁 보강의 두 독립 과정으로 바꾼다.
- [ ] 각 명령, 산출물, 실패 경계, 재시도 방법을 문서화한다.
- [ ] Cluedoc 다이어그램과 설명을 새 실행 경계에 맞춘다.
- [ ] 문서의 경로·명령·옵션이 실제 코드와 일치하는지 확인한다.

### Task 5: 통합 검증과 전달

**Files:**
- Verify only: changed files and test suites

- [ ] `services/ai` 타깃 테스트를 실행한다.
- [ ] `services/data` 런타임 테스트를 실행한다.
- [ ] 변경 Python 파일에 `ruff check`를 실행한다.
- [ ] 1건 dry-run 리포트 생성 결과에 툴팁 후보가 없는지 확인한다.
- [ ] 같은 manifest로 1건 툴팁 dry-run을 실행해 독립 산출물과 원문 보존을 확인한다.
- [ ] 변경 범위만 커밋하고 브랜치를 푸시한다.

### FACTS Validation

- [x] F: 기존 Codex 실행기, manifest, DB upsert 경로를 재사용하므로 현재 환경에서 구현 가능하다.
- [x] A: 각 Task는 생성 계약, 툴팁 실행기, 런타임 연결, 문서, 검증 중 하나만 담당한다.
- [x] C: 모든 Task에 대상 파일과 구체 동작이 명시돼 있다.
- [x] T: 실패 테스트, 타깃 pytest, ruff, 실제 dry-run 검증이 정의돼 있다.
- [x] S: 복수 의미 사전 개편과 웹 렌더러는 비범위로 고정했다.
