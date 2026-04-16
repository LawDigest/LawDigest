# -*- coding: utf-8 -*-
from __future__ import annotations

import sys

import pendulum

from airflow.models.dag import DAG
from airflow.models.param import Param
from airflow.operators.python import PythonOperator


PROJECT_ROOT = "/opt/airflow/project"


def _build_manager(execution_mode: str):
    if PROJECT_ROOT not in sys.path:
        sys.path.append(PROJECT_ROOT)

    from lawdigest_data.core.WorkFlowManager import WorkFlowManager

    return WorkFlowManager(execution_mode)


def run_status_step(method_name, **context):
    params = context.get("params", {})
    start_date = params.get("start_date")
    end_date = params.get("end_date")
    age = params.get("age")
    execution_mode = params.get("execution_mode") or "dry_run"

    manager = _build_manager(execution_mode)
    result = getattr(manager, method_name)(
        start_date=start_date,
        end_date=end_date,
        age=age,
    )

    print(f"--- Finished {method_name} ---")
    return result


def run_status_upsert(fetch_method_name, upsert_method_name, **context):
    params = context.get("params", {})
    start_date = params.get("start_date")
    end_date = params.get("end_date")
    age = params.get("age")
    execution_mode = params.get("execution_mode") or "dry_run"

    manager = _build_manager(execution_mode)
    fetched = getattr(manager, fetch_method_name)(
        start_date=start_date,
        end_date=end_date,
        age=age,
    )
    artifact_path = fetched.get("artifact_path")
    if not artifact_path:
        return {"mode": execution_mode, "step": upsert_method_name, "skipped": True}
    return getattr(manager, upsert_method_name)(artifact_path)


with DAG(
    dag_id="bill_status_sync_dag",
    schedule="0 * * * *",
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    tags=["bill", "sync", "hourly"],
    params={
        "execution_mode": Param(
            "dry_run",
            type="string",
            enum=["dry_run", "test_db", "prod"],
            title="실행 모드",
            description="dry_run: DB 미반영, test_db: 테스트 DB, prod: 운영 DB",
        ),
        "start_date": Param(
            None,
            type=["null", "string"],
            title="시작 날짜",
            description="데이터를 수집할 시작 날짜 (YYYY-MM-DD). 비워두면 checkpoint 또는 기본 기준일을 사용합니다.",
        ),
        "end_date": Param(
            None,
            type=["null", "string"],
            title="종료 날짜",
            description="데이터를 수집할 종료 날짜 (YYYY-MM-DD). 비워두면 오늘 날짜까지 가져옵니다.",
        ),
        "age": Param(
            "22",
            type="string",
            title="국회 대수",
            description="수집할 국회 대수 (기본값: 22)",
        ),
    },
    doc_md="""
    ## 법안 상태 동기화

    `assembly-api-mcp` 레퍼런스 기준으로 lifecycle 과 vote capability 를 분리해 동기화합니다.

    ### 태스크 순서
    `update_lawmakers` 이후 아래 두 파이프라인이 병렬 실행됩니다.

    - `fetch_lifecycle -> upsert_lifecycle`
    - `fetch_vote -> upsert_vote`
    """,
) as dag:
    update_lawmakers = PythonOperator(
        task_id="update_lawmakers",
        python_callable=run_status_step,
        op_kwargs={"method_name": "update_lawmakers_data"},
    )

    lifecycle_sync = PythonOperator(
        task_id="sync_lifecycle",
        python_callable=run_status_upsert,
        op_kwargs={
            "fetch_method_name": "fetch_lifecycle_step",
            "upsert_method_name": "upsert_lifecycle_step",
        },
    )

    vote_sync = PythonOperator(
        task_id="sync_vote",
        python_callable=run_status_upsert,
        op_kwargs={
            "fetch_method_name": "fetch_vote_step",
            "upsert_method_name": "upsert_vote_step",
        },
    )

    update_lawmakers >> [lifecycle_sync, vote_sync]
