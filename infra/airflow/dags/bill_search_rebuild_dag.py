# -*- coding: utf-8 -*-
from __future__ import annotations

import sys

import pendulum

from airflow.models.dag import DAG
from airflow.models.param import Param
from airflow.operators.python import PythonOperator


PROJECT_ROOT = "/opt/airflow/project"


def rebuild_bill_search_documents(**context):
    if PROJECT_ROOT not in sys.path:
        sys.path.append(PROJECT_ROOT)

    from lawdigest_data.core.WorkFlowManager import WorkFlowManager

    params = context.get("params", {})
    manager = WorkFlowManager(params.get("execution_mode") or "dry_run")
    return manager.rebuild_bill_search_documents(limit=params.get("limit") or 500)


with DAG(
    dag_id="bill_search_rebuild_dag",
    schedule="*/10 * * * *",
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    tags=["bill", "search", "rebuild"],
    params={
        "execution_mode": Param(
            "dry_run",
            type="string",
            enum=["dry_run", "test", "prod"],
            title="실행 모드",
            description="dry_run: DB 미반영, test: 테스트 DB, prod: 운영 DB",
        ),
        "limit": Param(
            500,
            type="integer",
            minimum=1,
            maximum=5000,
            title="최대 재빌드 건수",
        ),
    },
) as dag:
    rebuild = PythonOperator(
        task_id="rebuild_bill_search_documents",
        python_callable=rebuild_bill_search_documents,
    )
