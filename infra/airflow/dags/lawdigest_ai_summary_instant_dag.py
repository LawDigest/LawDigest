# -*- coding: utf-8 -*-
from __future__ import annotations

import json
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


def run_instant_ai_summary(**context):
    params = context.get("params", {})
    mode = params.get("execution_mode") or "dry_run"
    print(f"[ai-summary-instant] Current Mode: {mode}")

    bill_json = params.get("bill_json")
    if bill_json:
        try:
            bill_data = json.loads(bill_json)
        except json.JSONDecodeError as exc:
            raise ValueError(f"bill_json이 유효한 JSON이 아닙니다: {exc}") from exc
    else:
        bill_data = {
            "bill_id": params.get("bill_id"),
            "bill_name": params.get("bill_name"),
            "summary": params.get("summary"),
            "proposers": params.get("proposers"),
            "proposer_kind": params.get("proposer_kind"),
            "proposeDate": params.get("propose_date"),
            "stage": params.get("stage"),
        }

    if not bill_data.get("bill_id"):
        raise ValueError("bill_id는 필수입니다.")
    if not bill_data.get("summary"):
        raise ValueError("summary는 필수입니다.")

    project_root = "/opt/airflow/project"
    if project_root not in sys.path:
        sys.path.append(project_root)

    # 파서 단계 import 실패를 피하기 위해 실행 시점에 import
    from src.lawdigest_data_pipeline.WorkFlowManager import WorkFlowManager
    from src.lawdigest_data_pipeline.DatabaseManager import DatabaseManager
    from src.lawdigest_data_pipeline.ai_batch_pipeline_utils import (
        get_test_db_config,
        get_prod_db_config,
    )

    workflow = WorkFlowManager(mode="db")
    summarized_rows = workflow.summarize_bill_step(bill_data)

    if mode != "dry_run" and _as_bool(params.get("upsert", True)):
        if mode == "prod":
            db_cfg = get_prod_db_config()
            print("[ai-summary-instant] Using PRODUCTION database")
        else:
            db_cfg = get_test_db_config()
            print("[ai-summary-instant] Using TEST database")

        db = DatabaseManager(
            host=db_cfg["host"],
            port=db_cfg["port"],
            username=db_cfg["user"],
            password=db_cfg["password"],
            database=db_cfg["database"],
        )
        # WorkFlowManager의 upsert_bill_step 대신 명시적 DB 인스턴스 사용
        import pandas as pd
        bill_rows = [workflow._build_bill_row(pd.Series(r)) for r in summarized_rows]
        if bill_rows:
            db.insert_bill_info(bill_rows)
            print(f"[ai-summary-instant] [{mode}] DB upsert completed.")
    else:
        print(f"[ai-summary-instant] [{mode}] DB upsert skipped.")

    result = summarized_rows[0] if summarized_rows else {}
    print(json.dumps(result, ensure_ascii=False))
    return result


with DAG(
    dag_id="lawdigest_ai_summary_instant_dag",
    schedule=None,
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    tags=["lawdigest", "ai-summary", "instant"],
    params={
        "execution_mode": Param(
            "dry_run",
            type="string",
            enum=["dry_run", "test", "prod"],
            title="실행 모드",
            description="dry_run: DB 반영 안 함, test: 테스트 DB 사용, prod: 운영 DB 사용",
        ),
        "bill_json": Param(
...
        "upsert": Param(
            True,
            type="boolean",
            title="DB upsert",
            description="True면 요약 결과를 Bill 테이블에 즉시 반영 (dry_run 모드에서는 무시됨)",
        ),
    },
    doc_md="""
    ### Lawdigest AI Summary 즉시 실행 DAG

    - 스케줄링 없음 (`schedule=None`)
    - 수동 트리거로 단일 법안을 즉시 요약합니다.
    - `upsert=True`이면 요약 결과를 DB에 즉시 반영합니다.
    """,
) as dag:
    instant_ai_summary = PythonOperator(
        task_id="instant_ai_summary",
        python_callable=run_instant_ai_summary,
    )

