# Gemini AI Summary Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gemini CLI 기반 법안 요약을 기존 OpenAI batch 경로와 분리된 독립 Airflow 파이프라인으로 운영할 수 있게 만든다.

**Architecture:** Airflow DAG는 수동 실행용 진입점만 제공하고, 실제 동작은 재사용 가능한 Gemini repair pipeline 모듈이 맡는다. 이 모듈은 DB에서 미요약 법안을 조회하고, Gemini CLI 요약을 수행한 뒤 JSON 산출물을 저장하고 필요 시 DB에 upsert한다.

**Tech Stack:** Python, Airflow, pandas, pymysql, Gemini CLI ACP, pytest

---

### Task 1: Gemini repair pipeline 모듈 추가

**Files:**
- Create: `services/ai/src/lawdigest_ai/processor/gemini_repair_pipeline.py`

- [ ] DB에서 미요약 법안을 limit 기준으로 조회하는 함수 추가
- [ ] Gemini CLI 배치 처리 및 성공/실패 리포트 생성 함수 추가
- [ ] JSON 산출물 저장 및 test/prod DB upsert 로직 추가
- [ ] 전체 실패 시 예외를 발생시키고, 부분 실패는 보고서에 남기도록 정리

### Task 2: 독립 Airflow DAG 추가

**Files:**
- Create: `infra/airflow/dags/gemini_ai_summary_repair_dag.py`

- [ ] 새 pipeline 모듈을 호출하는 수동 DAG 추가
- [ ] execution_mode, limit, batch_size, output_path, stop_on_error 파라미터 정의
- [ ] Gemini 전용 독립 경로임을 doc_md에 문서화

### Task 3: 테스트 추가

**Files:**
- Create: `services/ai/tests/processor/test_gemini_repair_pipeline.py`

- [ ] dry_run에서 JSON 산출물만 저장하는 테스트 추가
- [ ] test/prod에서 성공 건 upsert를 호출하는 테스트 추가
- [ ] 전체 실패 시 예외를 내는 테스트 추가
