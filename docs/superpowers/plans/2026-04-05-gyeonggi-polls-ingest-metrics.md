# Gyeonggi Polls Ingest Metrics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 경기도 여론조사 수집 DAG를 `test` 모드로 실행하고 단계별 건수와 전체 실행시간을 로그, XCom, artifact로 남긴다.

**Architecture:** 기존 `PollsWorkflowManager` 단계 반환값에 계측 메타를 추가하고, DAG 끝에 얇은 `summarize_run` 태스크를 붙인다. 타깃 범위는 별도 경기도 전용 타깃 파일로 고정한다.

**Tech Stack:** Python, Airflow DAG, LawDigest data pipeline, pytest

---

### Task 1: 경기도 전용 타깃 파일 추가

**Files:**
- Create: `services/data/config/poll_targets.gyeonggi.json`

- [ ] 기존 `poll_targets.json` 구조를 기준으로 경기도 전용 타깃 파일을 추가한다.
- [ ] DAG 실행 시 이 파일을 넘길 수 있게 경로를 기록한다.

### Task 2: workflow 단계 계측 추가

**Files:**
- Modify: `services/data/src/lawdigest_data/polls/workflow.py`

- [ ] `fetch_polls_step`, `crawl_details_step`, `parse_results_step`, `upsert_polls_step`에 실행시간 측정을 넣는다.
- [ ] 단계 반환값에 `elapsed_seconds`와 핵심 건수를 추가한다.
- [ ] 기존 artifact payload 형식은 유지한다.

### Task 3: DAG 최종 요약 태스크 추가

**Files:**
- Modify: `infra/airflow/dags/polls_ingest_dag.py`

- [ ] `summarize_run` 태스크를 추가한다.
- [ ] 앞선 단계 XCom을 읽어 전체 실행시간과 총 건수를 집계한다.
- [ ] 요약 artifact를 생성하고 로그/XCom에 동일 내용을 남긴다.

### Task 4: 테스트 보강

**Files:**
- Modify: 관련 pytest 파일 탐색 후 최소 범위 수정

- [ ] 현재 DAG/workflow 테스트 위치를 확인한다.
- [ ] 계측 필드와 요약 집계를 검증하는 테스트를 추가하거나 갱신한다.
- [ ] 변경된 테스트만 먼저 실행해 통과를 확인한다.

### Task 5: 실제 실행 검증

**Files:**
- No code changes expected

- [ ] `polls_ingest_dag`를 `test` 모드와 경기도 전용 타깃 파일로 1회 실행한다.
- [ ] artifact 생성, 수집 결과 저장, 최종 요약 메타를 확인한다.
- [ ] 실패 시 로그와 artifact를 근거로 수정한다.
