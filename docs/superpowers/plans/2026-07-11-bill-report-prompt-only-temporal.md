# Bill Report Prompt-Only Temporal Handling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove temporal runtime gates, keep temporal guidance in the report prompt, and recognize target law names ending in both `법` and `법률`.

**Architecture:** Keep deterministic `bill_text` and `current_law` evidence as the only temporal inputs. Simplify output parsing and validation back to report-body and density concerns, while expanding the existing law-name regex without introducing a new abstraction.

**Tech Stack:** Python 3.13, pytest, Codex CLI JSON output

---

### Task 1: Lock the prompt-only contract and law-name extraction

**Files:**
- Modify: `services/ai/tests/processor/test_agentic_bill_report.py:24-410`

- [ ] Add a parameterized failing test for `...법` and `...법률` target names.
- [ ] Change the prompt contract test to require temporal instructions but reject `temporal_consistency` and `temporal_context` schema fields.
- [ ] Change evidence assertions to require only `bill_text` and `current_law` temporal sources.
- [ ] Run focused tests and confirm RED failures against the current implementation.

### Task 2: Remove temporal runtime logic and fix law-name extraction

**Files:**
- Modify: `services/ai/src/lawdigest_ai/processor/agentic_bill_report.py:53-60,488-503,676-810,1060-1125,1385-1390,1732-1810,2260-2505`

- [ ] Expand `_extract_target_law_names()` patterns to `(.+?(?:법률|법))`.
- [ ] Remove `_build_temporal_context()` and snapshot derivation from evidence.
- [ ] Replace temporal schema instructions with prompt-only prose.
- [ ] Simplify report parsing to return body and structured-output presence only.
- [ ] Replace `_validate_report_against_evidence()` with density-only validation.
- [ ] Run focused tests and confirm GREEN.

### Task 3: Update documentation and verify

**Files:**
- Modify: `docs/ai/bill-report-agent-pipeline.md`
- Modify: `docs/ai/bill-report-agent-prompt-contract.md`

- [ ] Document prompt-only temporal handling and expanded law-name extraction.
- [ ] Run `uvx ruff check` on modified Python files.
- [ ] Run the full `test_agentic_bill_report.py` suite.
- [ ] Run `git diff --check`.

### Task 4: Regenerate the seven failed reports

**Files:**
- Generated output only under `output/bills/`.

- [ ] Run the seven failed IDs with `mode=prod`, `concurrency=7`, `batch_session_size=1`, inspection enabled.
- [ ] Verify success count, DB upserts, current-law evidence, content isolation, and remaining passed target count.
- [ ] Commit and push source, tests, and documentation only.
