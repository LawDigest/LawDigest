# -*- coding: utf-8 -*-
from __future__ import annotations

import sys

import pendulum

from airflow.models.dag import DAG
from airflow.models.param import Param
from airflow.operators.python import PythonOperator


def fetch_bills_from_api(**context):
    project_root = "/opt/airflow/project"
    if project_root not in sys.path:
        sys.path.append(project_root)

    from src.lawdigest_data_pipeline.WorkFlowManager import WorkFlowManager

    params = context.get("params", {})
    manager = WorkFlowManager(params.get("execution_mode") or "dry_run")
    return manager.fetch_bills_data_step(
        start_date=params.get("start_date"),
        end_date=params.get("end_date"),
        age=params.get("age"),
    )


def process_fetched_bills(**context):
    project_root = "/opt/airflow/project"
    if project_root not in sys.path:
        sys.path.append(project_root)

    from src.lawdigest_data_pipeline.WorkFlowManager import WorkFlowManager

    params = context.get("params", {})
    task_instance = context["ti"]
    fetched = task_instance.xcom_pull(task_ids="fetch_bills_from_api") or {}
    artifact_path = fetched.get("artifact_path")
    if not artifact_path:
        return {"mode": params.get("execution_mode") or "dry_run", "processed": 0, "artifact_path": None}

    manager = WorkFlowManager(params.get("execution_mode") or "dry_run")
    return manager.process_bills_data_step(artifact_path)


def upsert_processed_bills(**context):
    project_root = "/opt/airflow/project"
    if project_root not in sys.path:
        sys.path.append(project_root)

    from src.lawdigest_data_pipeline.WorkFlowManager import WorkFlowManager

    params = context.get("params", {})
    task_instance = context["ti"]
    processed = task_instance.xcom_pull(task_ids="process_bills") or {}
    artifact_path = processed.get("artifact_path")
    if not artifact_path:
        return {"mode": params.get("execution_mode") or "dry_run", "upserted": 0}

    manager = WorkFlowManager(params.get("execution_mode") or "dry_run")
    return manager.upsert_bills_data_step(artifact_path)


with DAG(
    dag_id="bill_ingest_dag",
    schedule="0 * * * *",
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    tags=["lawdigest", "ingest", "api"],
    params={
        "execution_mode": Param(
            "dry_run",
            type="string",
            enum=["dry_run", "test", "prod"],
            title="실행 모드",
            description="dry_run: DB 미반영, test: 테스트 DB, prod: 운영 DB",
        ),
        "start_date": Param(
            None,
            type=["null", "string"],
            title="시작일",
            description="YYYY-MM-DD. 비우면 오늘 날짜",
        ),
        "end_date": Param(
            None,
            type=["null", "string"],
            title="종료일",
            description="YYYY-MM-DD. 비우면 오늘 날짜",
        ),
        "age": Param("22", type="string", title="국회 대수"),
    },
    doc_md="""
    ## 📑 Lawdigest 법안 수집 파이프라인 (Open API)

    국회 의안 API(Open API)로부터 최신 법안 데이터를 정기적으로 수집하여 데이터베이스에 반영하는 핵심 DAG입니다.

    ### 🚀 주요 기능
    1. **데이터 수집**: 지정된 기간 및 국회 대수(`age`)에 해당하는 법안 정보를 국회 API에서 가져옵니다.
    2. **데이터 매핑**: API 응답 데이터를 내부 DB 스키마(`Bill` 테이블 등)에 맞게 변환합니다.
    3. **DB 반영**: 중복을 체크하여 신규 법안은 추가하고, 기존 법안은 최신 상태로 업데이트(Upsert)합니다.

    ### ⚙️ 실행 모드 (Execution Mode)
    - `dry_run` (기본값): 실제 DB에 데이터를 쓰지 않고, 수집된 데이터의 양과 내용만 로그로 확인합니다. 안전한 테스트를 위해 권장됩니다.
    - `test`: 프로젝트의 테스트용 데이터베이스(`TEST_DB_*` 환경변수)에 수집 결과를 반영합니다.
    - `prod`: 실제 서비스가 운영되는 프로덕션 데이터베이스(`DB_*` 환경변수)에 즉시 반영합니다.

    ### 📅 파라미터 가이드
    - `execution_mode`: 실행 환경 선택 (dry_run, test, prod)
    - `start_date`: 수집 시작일 (YYYY-MM-DD). 비워두면 오늘 날짜 기준.
    - `end_date`: 수집 종료일 (YYYY-MM-DD). 비워두면 오늘 날짜 기준.
    - `age`: 수집 대상 국회 대수 (기본값: 22)

    ---
    *주의: 수집된 법안은 원문 그대로 저장되며, AI 요약은 별도 DAG에서 수행됩니다.*
    """,
) as dag:
    fetch_bills = PythonOperator(
        task_id="fetch_bills_from_api",
        python_callable=fetch_bills_from_api,
    )

    process_bills = PythonOperator(
        task_id="process_bills",
        python_callable=process_fetched_bills,
    )

    upsert_bills = PythonOperator(
        task_id="upsert_bills",
        python_callable=upsert_processed_bills,
    )

    fetch_bills >> process_bills >> upsert_bills
