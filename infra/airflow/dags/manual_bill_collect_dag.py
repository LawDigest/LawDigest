# -*- coding: utf-8 -*-
from __future__ import annotations

import sys

import pendulum

from airflow.models.dag import DAG
from airflow.models.param import Param
from airflow.operators.python import PythonOperator


def fetch_manual_bills(**context):
    project_root = "/opt/airflow/project"
    if project_root not in sys.path:
        sys.path.append(project_root)

    from lawdigest_data.core.WorkFlowManager import WorkFlowManager

    params = context.get("params", {})
    start_date = params.get("start_date")
    end_date = params.get("end_date")
    age = params.get("age")
    execution_mode = params.get("execution_mode") or "prod"

    manager = WorkFlowManager(execution_mode)
    print(
        "Airflow-triggered execution with params: "
        f"start_date={start_date}, end_date={end_date}, age={age}, execution_mode={execution_mode}"
    )
    return manager.fetch_bills_data_step(
        start_date=start_date,
        end_date=end_date,
        age=age,
    )


def process_manual_bills(**context):
    project_root = "/opt/airflow/project"
    if project_root not in sys.path:
        sys.path.append(project_root)

    from lawdigest_data.core.WorkFlowManager import WorkFlowManager

    params = context.get("params", {})
    task_instance = context["ti"]
    fetched = task_instance.xcom_pull(task_ids="fetch_manual_bills") or {}
    artifact_path = fetched.get("artifact_path")
    if not artifact_path:
        return {"mode": params.get("execution_mode") or "prod", "processed": 0, "artifact_path": None}

    manager = WorkFlowManager(params.get("execution_mode") or "prod")
    return manager.process_bills_data_step(artifact_path)


def upsert_manual_bills(**context):
    project_root = "/opt/airflow/project"
    if project_root not in sys.path:
        sys.path.append(project_root)

    from lawdigest_data.core.WorkFlowManager import WorkFlowManager

    params = context.get("params", {})
    task_instance = context["ti"]
    processed = task_instance.xcom_pull(task_ids="process_manual_bills") or {}
    artifact_path = processed.get("artifact_path")
    if not artifact_path:
        return {"mode": params.get("execution_mode") or "prod", "upserted": 0}

    manager = WorkFlowManager(params.get("execution_mode") or "prod")
    return manager.upsert_bills_data_step(artifact_path)


with DAG(
    dag_id="manual_bill_collect_dag",
    schedule=None,
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    tags=["lawdigest", "manual-run", "tools"],
    params={
        "execution_mode": Param(
            "prod",
            type="string",
            enum=["dry_run", "test", "prod"],
            title="실행 모드",
            description="dry_run: DB 미반영, test: 테스트 DB, prod: 운영 DB",
        ),
        "start_date": Param(
            None,
            type=["null", "string"],
            title="시작 날짜",
            description="수집할 시작 날짜 (YYYY-MM-DD)",
        ),
        "end_date": Param(
            None,
            type=["null", "string"],
            title="종료 날짜",
            description="수집할 종료 날짜 (YYYY-MM-DD)",
        ),
        "age": Param(
            "22",
            type="string",
            title="국회 대수",
            description="수집할 국회 대수",
        ),
    },
    doc_md="""
    ## 🛠️ Lawdigest 수동 법안 데이터 수집 도구

    스케줄에 의존하지 않고, 사용자가 직접 범위를 지정하여 법안 데이터를 강제 수집할 때 사용하는 도구용 DAG입니다.

    ### 🚀 주요 기능
    1. **범위 지정 수집**: `start_date`와 `end_date`를 지정하여 특정 기간의 법안을 수집합니다.
    2. **국회 대수 선택**: 특정 국회 대수(`age`)를 지정하여 대량 수집이 가능합니다.
    3. **실행 모드 선택**: `dry_run`, `test`, `prod` 중 하나를 골라 수집 결과의 반영 위치를 정합니다.

    ### ⚙️ 실행 방법
    - **수동 실행 전용** (`schedule=None`)
    - `Trigger DAG w/ Config`를 통해 파라미터를 입력하고 실행하세요.

    ### 📅 파라미터 가이드
    - `execution_mode`: `dry_run`, `test`, `prod`
    - `start_date`: 수집 시작 날짜 (YYYY-MM-DD)
    - `end_date`: 수집 종료 날짜 (YYYY-MM-DD)
    - `age`: 국회 대수 (예: 21, 22)

    ---
    *주의: 대량 데이터를 수집할 때는 API 속도 제한이나 DB 부하를 고려하여 적절한 기간으로 나누어 실행하십시오.*
    """,
) as dag:
    fetch_bills = PythonOperator(
        task_id="fetch_manual_bills",
        python_callable=fetch_manual_bills,
    )

    process_bills = PythonOperator(
        task_id="process_manual_bills",
        python_callable=process_manual_bills,
    )

    upsert_bills = PythonOperator(
        task_id="upsert_manual_bills",
        python_callable=upsert_manual_bills,
    )

    fetch_bills >> process_bills >> upsert_bills
