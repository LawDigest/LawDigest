# -*- coding: utf-8 -*-
"""NESDC 여론조사 전체 카탈로그 스캔 DAG.

NESDC 사이트를 전체 페이지 스캔하여 존재하는 (선거구분, 지역, 선거명, 조사기관)
조합을 수집하고 PollCatalog 테이블에 저장한다.
이 DAG를 먼저 실행하여 catalog_path 결과를 확인한 뒤, poll_targets.json에
수집 대상을 지정하면 된다.
"""
from __future__ import annotations

import sys

import pendulum

from airflow.models.dag import DAG
from airflow.models.param import Param
from airflow.operators.python import PythonOperator

_PROJECT_ROOT = "/opt/airflow/project"


def catalog_scan(**context):
    if _PROJECT_ROOT not in sys.path:
        sys.path.append(_PROJECT_ROOT)

    from src.lawdigest_data_pipeline.polls.workflow import PollsWorkflowManager

    params = context.get("params", {})
    manager = PollsWorkflowManager(params.get("execution_mode") or "dry_run")
    return manager.catalog_scan_step(
        max_pages=int(params.get("max_pages") or 500),
    )


def save_catalog(**context):
    if _PROJECT_ROOT not in sys.path:
        sys.path.append(_PROJECT_ROOT)

    from src.lawdigest_data_pipeline.polls.workflow import PollsWorkflowManager

    params = context.get("params", {})
    task_instance = context["ti"]
    scanned = task_instance.xcom_pull(task_ids="catalog_scan") or {}
    artifact_path = scanned.get("artifact_path")

    manager = PollsWorkflowManager(params.get("execution_mode") or "dry_run")
    return manager.save_catalog_step(artifact_path=artifact_path)


with DAG(
    dag_id="polls_catalog_dag",
    schedule="0 2 * * 0",  # 매주 일요일 새벽 2시
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    tags=["lawdigest", "polls", "catalog"],
    params={
        "execution_mode": Param(
            "dry_run",
            type="string",
            enum=["dry_run", "test", "prod"],
            title="실행 모드",
            description="dry_run: DB 미반영, test: 테스트 DB, prod: 운영 DB",
        ),
        "max_pages": Param(
            500,
            type="integer",
            title="최대 스캔 페이지 수",
            description="NESDC 전체 스캔 시 최대 페이지 수 (기본값: 500)",
        ),
    },
    doc_md="""
    ## 📊 NESDC 여론조사 카탈로그 스캔 DAG

    NESDC(중앙선거여론조사심의위원회) 사이트를 전체 스캔하여 어떤 여론조사 데이터가
    존재하는지 목록을 만드는 DAG입니다.

    ### 🚀 주요 기능
    1. **전체 페이지 스캔**: NESDC 사이트를 처음부터 끝까지 스캔하여 모든 여론조사 목록을 수집합니다.
    2. **카탈로그 생성**: 고유한 (선거구분, 지역, 선거명, 조사기관) 조합을 추출하여 저장합니다.
    3. **DB 저장**: `PollCatalog` 테이블에 upsert합니다 (prod/test 모드).

    ### 📋 활용 방법
    1. 이 DAG를 먼저 `dry_run` 모드로 실행합니다.
    2. `save_catalog` 태스크의 XCom 출력(`catalog_path`)에서 JSON 파일을 확인합니다.
    3. JSON 파일의 `election_types`, `regions`, `election_names`, `pollsters` 값을 참고하여
       `config/poll_targets.json`에 수집 대상을 지정합니다.
    4. `polls_ingest_dag`를 실행하여 지정된 타겟만 수집합니다.

    ### ⚙️ 실행 모드
    - `dry_run` (기본값): DB 미반영, 카탈로그 artifact JSON만 생성
    - `test`: 테스트 DB에 반영
    - `prod`: 운영 DB에 반영
    """,
) as dag:
    t_scan = PythonOperator(
        task_id="catalog_scan",
        python_callable=catalog_scan,
    )

    t_save = PythonOperator(
        task_id="save_catalog",
        python_callable=save_catalog,
    )

    t_scan >> t_save
