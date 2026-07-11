# Bill Report Temporal and Density Validation Implementation Plan

> Superseded: 시점 게이트 구현은 철회됐으며 `2026-07-11-bill-report-prompt-only-temporal.md`가 현재 계획이다. 분량 검증 변경만 유효하다.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent proposal-time/current-law contradictions and keep Luna reports proportional to each bill's actual change complexity.

**Architecture:** Extend the deterministic evidence packet with temporal and density metadata, require a same-turn structured temporal self-check, and validate the final Markdown against those contracts before DB persistence. Reuse the existing validation failure classification and per-item retry path.

**Tech Stack:** Python 3.13, pytest, Codex CLI structured JSON output

---

### Task 1: Define temporal and density evidence contracts

**Files:**
- Modify: `services/ai/src/lawdigest_ai/processor/agentic_bill_report.py:645-728`
- Test: `services/ai/tests/processor/test_agentic_bill_report.py`

- [x] Write failing tests for simple/complex density classification and temporal source metadata.
- [x] Run the focused tests and confirm missing metadata failures.
- [x] Add `_build_report_density()` and temporal metadata to `build_bill_report_evidence()`.
- [x] Run the focused tests and confirm they pass.

### Task 2: Require structured temporal consistency output

**Files:**
- Modify: `services/ai/src/lawdigest_ai/processor/agentic_bill_report.py:40-135, 983-1038, 1271-1313`
- Test: `services/ai/tests/processor/test_agentic_bill_report.py`

- [x] Write failing tests that require `temporal_consistency.confidence=high` in single and batch output.
- [x] Run the focused tests and confirm the current parser accepts missing metadata.
- [x] Extend prompt schemas and parsing so the selected report payload remains available for validation.
- [x] Run the focused tests and confirm high passes while missing/low fails.

### Task 3: Validate temporal wording and density

**Files:**
- Modify: `services/ai/src/lawdigest_ai/processor/agentic_bill_report.py:1658-1753, 2158-2193, 2327-2345`
- Test: `services/ai/tests/processor/test_agentic_bill_report.py`

- [x] Write failing tests for unqualified `현행법` in passed bills, qualified proposal-time wording, simple report section count, and the 3,600-character maximum.
- [x] Run the focused tests and confirm each fails for the intended missing behavior.
- [x] Add `_validate_report_against_evidence()` and call it before marking a report successful.
- [x] Run the focused tests and confirm all pass.

### Task 4: Update operating documentation

**Files:**
- Modify: `docs/ai/bill-report-agent-pipeline.md`
- Modify: `docs/ai/bill-report-agent-prompt-contract.md`

- [x] Document temporal evidence roles, structured confidence gate, density classes, and retry behavior.
- [x] Run `git diff --check`.

### Task 5: Verify and smoke test

**Files:**
- No production file changes expected.

- [x] Run `uvx ruff check` on the modified Python files.
- [x] Run the full `test_agentic_bill_report.py` suite.
- [x] Run one Luna `dry_run --read-mode prod --inspection` smoke with one session and one bill.
- [x] Inspect manifest, report body, temporal gate metadata, length, section count, retry count, and DB upsert count.
- [x] Commit and push only source, tests, and documentation; leave experiment output untracked.
