# -*- coding: utf-8 -*-
from __future__ import annotations

import pendulum
import sys

from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
from airflow.models.param import Param


def run_workflow_step(method_name, **context):
    params = context.get("params", {})
    start_date = params.get("start_date")
    end_date = params.get("end_date")
    age = params.get("age")

    print(f"--- Calling {method_name} ---")
    if start_date or end_date:
        print(f"Custom range detected: {start_date} ~ {end_date} (Age: {age})")
    else:
        print("No custom range detected. Using default scheduling/latest data logic.")

    from src.lawdigest_data_pipeline.WorkFlowManager import WorkFlowManager

    wfm = WorkFlowManager(mode='remote')
    method = getattr(wfm, method_name)

    if method_name == "update_lawmakers_data":
        method()
    else:
        method(start_date=start_date, end_date=end_date, age=age)

    print(f"--- Finished {method_name} ---")


with DAG(
    dag_id="bill_status_sync_dag",
    schedule="0 * * * *",  # 매 정시 실행
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    tags=["bill", "sync", "hourly"],
    params={
        "start_date": Param(
            None,
            type=["null", "string"],
            title="시작 날짜",
            description="데이터를 수집할 시작 날짜 (YYYY-MM-DD). 비워두면 최신 데이터부터 가져옵니다.",
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
    ## 🔄 법안 상태 동기화

    매시간 법안의 타임라인, 처리 결과, 표결 정보, 의원 정보를 최신 상태로 동기화합니다.
    법안 기본 수집은 `bill_ingest_dag`가 담당합니다.

    ### 태스크 순서
    `update_lawmakers` → `update_timeline`, `update_results`, `update_votes` (병렬)

    ### 파라미터
    - `start_date`: 시작 날짜 (YYYY-MM-DD, 선택)
    - `end_date`: 종료 날짜 (YYYY-MM-DD, 선택)
    - `age`: 국회 대수 (기본값: 22)
    """,
) as dag:

    update_lawmakers = PythonOperator(
        task_id="update_lawmakers",
        python_callable=run_workflow_step,
        op_kwargs={"method_name": "update_lawmakers_data"},
    )

    update_timeline = PythonOperator(
        task_id="update_timeline",
        python_callable=run_workflow_step,
        op_kwargs={"method_name": "update_bills_timeline"},
    )

    update_results = PythonOperator(
        task_id="update_results",
        python_callable=run_workflow_step,
        op_kwargs={"method_name": "update_bills_result"},
    )

    update_votes = PythonOperator(
        task_id="update_votes",
        python_callable=run_workflow_step,
        op_kwargs={"method_name": "update_bills_vote"},
    )

    # 의원 정보 갱신 후 타임라인/결과/표결 병렬 실행
    update_lawmakers >> [update_timeline, update_results, update_votes]
