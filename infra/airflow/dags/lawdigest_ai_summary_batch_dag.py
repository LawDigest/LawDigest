# -*- coding: utf-8 -*-
from __future__ import annotations

import sys

import pendulum

from airflow.models.dag import DAG
from airflow.models.param import Param
from airflow.operators.python import PythonOperator


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "y", "yes", "on"}
    return False


def run_batch_ai_summary(**context):
    params = context.get("params", {})
    output_path = params.get("output_path") or "/tmp/lawdigest_missing_summaries.json"
    batch_size = int(params.get("batch_size") or 10)
    mode = params.get("execution_mode") or "dry_run"
    dry_run = (mode == "dry_run")

    print(f"[ai-summary-batch] Current Mode: {mode}")

    project_root = "/opt/airflow/project"
    if project_root not in sys.path:
        sys.path.append(project_root)

    # 파서 단계 import 실패를 피하기 위해 실행 시점에 import
    from scripts.find_missing_summaries import find_missing_summaries
    from scripts.repair_missing_summaries import repair_missing_summaries
    from src.lawdigest_data_pipeline.ai_batch_pipeline_utils import (
        get_test_db_config,
        get_prod_db_config,
    )

    if mode == "prod":
        db_cfg = get_prod_db_config()
        print("[ai-summary-batch] Using PRODUCTION database")
    else:
        db_cfg = get_test_db_config()
        print("[ai-summary-batch] Using TEST database")

    find_missing_summaries(output_path=output_path, db_config=db_cfg)
    repair_missing_summaries(
        input_path=output_path,
        dry_run=dry_run,
        batch_size=batch_size,
        db_config=db_cfg,
    )


with DAG(
    dag_id="lawdigest_ai_summary_batch_dag",
    schedule=None,
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    tags=["lawdigest", "ai-summary", "batch"],
    params={
        "execution_mode": Param(
            "dry_run",
            type="string",
            enum=["dry_run", "test", "prod"],
            title="실행 모드",
            description="dry_run: DB 업데이트 안 함, test: 테스트 DB 사용, prod: 운영 DB 사용",
        ),
        "output_path": Param(
            "/tmp/lawdigest_missing_summaries.json",
            type="string",
            title="결측치 JSON 경로",
            description="결측치 추출/복구 작업에 사용할 JSON 파일 경로",
        ),
        "batch_size": Param(
            10,
            type="integer",
            title="배치 크기",
            description="한 번에 처리할 법안 수",
        ),
    },
    doc_md="""
    ### Lawdigest AI Summary 배치 처리 DAG

    - 스케줄링 없음 (`schedule=None`)
    - 수동 트리거 시:
      1. DB에서 AI 요약 결측 법안 조회
      2. 결측치에 대해 AI 요약 배치 복구 수행
      3. 실행 모드(dry_run, test, prod)에 따라 DB 연동 방식 결정
    """,
) as dag:
    batch_ai_summary = PythonOperator(
        task_id="batch_ai_summary_repair",
        python_callable=run_batch_ai_summary,
    )

