# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime

import pendulum

from airflow.models.dag import DAG
from airflow.models.param import Param
from airflow.operators.python import PythonOperator


def ingest_bills_from_api(**context):
    params = context.get("params", {})
    start_date = params.get("start_date")
    end_date = params.get("end_date")
    age = str(params.get("age") or "22")
    mode = params.get("execution_mode") or "dry_run"

    print(f"[ingest] Current Mode: {mode}")

    today = datetime.now().strftime("%Y-%m-%d")
    start_date = start_date or today
    end_date = end_date or today

    project_root = "/opt/airflow/project"
    if project_root not in sys.path:
        sys.path.append(project_root)

    from src.lawdigest_data_pipeline.DatabaseManager import DatabaseManager
    from src.lawdigest_data_pipeline.ai_batch_pipeline_utils import (
        get_test_db_config,
        get_prod_db_config,
    )

    cmd = [
        "python",
        "/opt/airflow/project/scripts/run_n8n_bills_stage.py",
        "--stage",
        "fetch",
        "--start-date",
        start_date,
        "--end-date",
        end_date,
        "--age",
        age,
    ]
    print(f"[ingest] Fetching data for {start_date} to {end_date}, age={age}")
    completed = subprocess.run(cmd, capture_output=True, text=True, check=True)
    rows = json.loads(completed.stdout.strip() or "[]")
    if not rows:
        print("[ingest] 수집된 법안이 없습니다.")
        return {"fetched": 0, "upserted": 0, "mode": mode}

    if mode == "dry_run":
        print(f"[ingest] [DRY_RUN] {len(rows)}개의 법안을 수집했으나 DB에 반영하지 않습니다.")
        return {"fetched": len(rows), "upserted": 0, "mode": "dry_run"}

    mapped = []
    for row in rows:
        proposer_kind = str(row.get("proposerKind") or "").strip()
        if proposer_kind == "의원":
            proposer_kind = "CONGRESSMAN"
        elif proposer_kind == "위원장":
            proposer_kind = "CHAIRMAN"
        elif proposer_kind == "정부":
            proposer_kind = "GOVERNMENT"

        mapped.append(
            {
                "bill_id": row.get("billId"),
                "bill_name": row.get("billName"),
                "committee": row.get("committee"),
                "gpt_summary": None,
                "propose_date": row.get("proposeDate"),
                "summary": row.get("summary"),
                "stage": row.get("stage"),
                "proposers": row.get("proposers"),
                "bill_pdf_url": row.get("billPdfUrl"),
                "brief_summary": None,
                "summary_tags": None,
                "bill_number": int(row.get("billNumber") or 0),
                "bill_link": row.get("bill_link"),
                "bill_result": row.get("billResult"),
                "proposer_kind": proposer_kind,
                "public_proposer_ids": row.get("publicProposerIdList") or [],
                "rst_proposer_ids": row.get("rstProposerIdList") or [],
            }
        )

    # 모드에 따른 DB 설정 선택
    if mode == "prod":
        db_cfg = get_prod_db_config()
        print("[ingest] Using PRODUCTION database")
    else:
        db_cfg = get_test_db_config()
        print("[ingest] Using TEST database")

    db = DatabaseManager(
        host=db_cfg["host"],
        port=db_cfg["port"],
        username=db_cfg["user"],
        password=db_cfg["password"],
        database=db_cfg["database"],
    )
    db.insert_bill_info(mapped)

    print(f"[ingest] [{mode}] fetched={len(rows)} upserted={len(mapped)}")
    return {"fetched": len(rows), "upserted": len(mapped), "mode": mode}


with DAG(
    dag_id="lawdigest_bill_ingest_dag",
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
    ### Lawdigest 법안 수집 DAG

    - 매시간 법안 API에서 원문 데이터를 수집합니다.
    - **실행 모드 선택 가능**:
        - `dry_run`: 수집만 수행하고 DB에는 저장하지 않습니다.
        - `test`: 테스트용 DB(`TEST_DB_*`)에 저장합니다.
        - `prod`: 운영용 DB(`DB_*`)에 저장합니다.
    """,
) as dag:
    ingest_bills = PythonOperator(
        task_id="ingest_bills_from_api",
        python_callable=ingest_bills_from_api,
    )
