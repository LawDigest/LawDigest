# -*- coding: utf-8 -*-
"""선거 데이터 수집 DAG.

중앙선거관리위원회 OpenAPI에서 코드정보, 후보자, 당선인, 공약, 정당정책을
매일 수집하여 DB에 저장한다.

수집 순서 (DAG):
  코드정보 → 후보자(예비+확정) → 당선인 → 공약+정당정책 → 요약
"""
from __future__ import annotations

import sys
from time import monotonic

import pendulum

from airflow.models.dag import DAG
from airflow.models.param import Param
from airflow.operators.python import PythonOperator

_PROJECT_ROOT = "/opt/airflow/project"
_DATA_SRC = f"{_PROJECT_ROOT}/services/data/src"
_RUN_STARTED_AT: float | None = None

# 제9회 전국동시지방선거
_DEFAULT_SG_ID = "20260603"


def _ensure_path():
    for p in (_PROJECT_ROOT, _DATA_SRC):
        if p not in sys.path:
            sys.path.append(p)


def collect_codes(**context):
    global _RUN_STARTED_AT
    _RUN_STARTED_AT = monotonic()
    _ensure_path()

    from lawdigest_data.elections.workflow import ElectionWorkflowManager

    params = context.get("params", {})
    manager = ElectionWorkflowManager(params.get("execution_mode") or "dry_run")
    return manager.collect_codes_step(sg_id=params.get("sg_id") or _DEFAULT_SG_ID)


def collect_candidates(**context):
    _ensure_path()

    from lawdigest_data.elections.workflow import ElectionWorkflowManager

    params = context.get("params", {})
    manager = ElectionWorkflowManager(params.get("execution_mode") or "dry_run")
    return manager.collect_candidates_step(sg_id=params.get("sg_id") or _DEFAULT_SG_ID)


def collect_winners(**context):
    _ensure_path()

    from lawdigest_data.elections.workflow import ElectionWorkflowManager

    params = context.get("params", {})
    manager = ElectionWorkflowManager(params.get("execution_mode") or "dry_run")
    return manager.collect_winners_step(sg_id=params.get("sg_id") or _DEFAULT_SG_ID)


def collect_pledges(**context):
    _ensure_path()

    from lawdigest_data.elections.workflow import ElectionWorkflowManager

    params = context.get("params", {})
    manager = ElectionWorkflowManager(params.get("execution_mode") or "dry_run")
    return manager.collect_pledges_step(sg_id=params.get("sg_id") or _DEFAULT_SG_ID)


def summarize_run(**context):
    _ensure_path()

    from lawdigest_data.elections.workflow import _write_artifact

    params = context.get("params", {})
    ti = context["ti"]
    codes = ti.xcom_pull(task_ids="collect_codes") or {}
    candidates = ti.xcom_pull(task_ids="collect_candidates") or {}
    winners = ti.xcom_pull(task_ids="collect_winners") or {}
    pledges = ti.xcom_pull(task_ids="collect_pledges") or {}

    started_at = _RUN_STARTED_AT
    total_elapsed = round(monotonic() - started_at, 3) if started_at is not None else None

    summary = {
        "mode": params.get("execution_mode") or "dry_run",
        "sg_id": params.get("sg_id") or _DEFAULT_SG_ID,
        "codes": codes.get("results", {}),
        "candidates": candidates.get("results", {}),
        "winners": winners.get("results", {}),
        "pledges": pledges.get("results", {}),
        "total_elapsed_seconds": total_elapsed,
        "step_elapsed_seconds": {
            "collect_codes": codes.get("elapsed_seconds"),
            "collect_candidates": candidates.get("elapsed_seconds"),
            "collect_winners": winners.get("elapsed_seconds"),
            "collect_pledges": pledges.get("elapsed_seconds"),
        },
        "artifacts": {
            "codes": codes.get("artifact_path"),
            "candidates": candidates.get("artifact_path"),
            "winners": winners.get("artifact_path"),
            "pledges": pledges.get("artifact_path"),
        },
    }
    summary["artifact_path"] = _write_artifact("election_ingest_summary", summary)
    print(f"[election_ingest.summary] {summary}")
    return summary


with DAG(
    dag_id="election_ingest_dag",
    schedule="0 4 * * *",  # 매일 새벽 4시
    start_date=pendulum.datetime(2026, 4, 1, tz="Asia/Seoul"),
    catchup=False,
    tags=["lawdigest", "election", "ingest"],
    params={
        "execution_mode": Param(
            "dry_run",
            type="string",
            enum=["dry_run", "test", "prod"],
            title="실행 모드",
            description="dry_run: DB 미반영, test: 테스트 DB, prod: 운영 DB",
        ),
        "sg_id": Param(
            _DEFAULT_SG_ID,
            type="string",
            title="선거 ID",
            description="수집 대상 선거 ID (기본값: 제9회 지방선거 20260603)",
        ),
    },
    doc_md="""
    ## 🗳️ 선거 데이터 수집 DAG

    중앙선거관리위원회 OpenAPI 5개 서비스에서 선거 데이터를 수집하여 DB에 저장합니다.

    ### 📋 수집 순서
    1. **코드정보** — 선거코드, 선거구, 구시군, 정당, 직업, 학력 코드 (6종)
    2. **후보자** — 예비후보자 + 확정후보자
    3. **당선인** — 당선인 정보 + 후보자 FK 연결
    4. **공약/정책** — 선거공약 (sgTypecode 1,3,4,11) + 정당정책

    ### ⚙️ 실행 모드
    - `dry_run` (기본값): API 샘플 조회만 수행, DB 미반영
    - `test`: 테스트 DB에 반영
    - `prod`: 운영 DB에 반영

    ### 🔗 데이터 연계
    - `election_candidates.normalized_region` → `PollSurvey.region` 으로 여론조사 연계
    - `election_winners.candidate_id` → `election_candidates.id` FK 자동 연결

    ### 📅 스케줄
    - 매일 새벽 4시 실행 (예비후보자 변동 감지)
    - 선거 종료 후 당선인/공약 데이터 자동 수집
    """,
) as dag:
    t_codes = PythonOperator(
        task_id="collect_codes",
        python_callable=collect_codes,
    )

    t_candidates = PythonOperator(
        task_id="collect_candidates",
        python_callable=collect_candidates,
    )

    t_winners = PythonOperator(
        task_id="collect_winners",
        python_callable=collect_winners,
    )

    t_pledges = PythonOperator(
        task_id="collect_pledges",
        python_callable=collect_pledges,
    )

    t_summary = PythonOperator(
        task_id="summarize_run",
        python_callable=summarize_run,
    )

    t_codes >> t_candidates >> t_winners >> t_pledges >> t_summary
