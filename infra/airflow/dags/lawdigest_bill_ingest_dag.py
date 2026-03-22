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

    today = datetime.now().strftime("%Y-%m-%d")
    start_date = start_date or today
    end_date = end_date or today

    project_root = "/opt/airflow/project"
    if project_root not in sys.path:
        sys.path.append(project_root)

    from src.lawdigest_data_pipeline.DatabaseManager import DatabaseManager
    from src.lawdigest_data_pipeline.ai_batch_pipeline_utils import get_test_db_config

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
    completed = subprocess.run(cmd, capture_output=True, text=True, check=True)
    rows = json.loads(completed.stdout.strip() or "[]")
    if not rows:
        print("[ingest] 수집된 법안이 없습니다.")
        return {"fetched": 0, "upserted": 0}

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

    db_cfg = get_test_db_config()
    db = DatabaseManager(
        host=db_cfg["host"],
        port=db_cfg["port"],
        username=db_cfg["user"],
        password=db_cfg["password"],
        database=db_cfg["database"],
    )
    db.insert_bill_info(mapped)

    print(f"[ingest] fetched={len(rows)} upserted={len(mapped)}")
    return {"fetched": len(rows), "upserted": len(mapped)}


with DAG(
    dag_id="lawdigest_bill_ingest_dag",
    schedule="0 * * * *",
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    tags=["lawdigest", "ingest", "api", "test-db"],
    params={
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
    ### Lawdigest 법안 수집 DAG (테스트 DB)

    - 매시간 법안 API에서 원문 데이터를 수집합니다.
    - AI 요약은 수행하지 않고 Bill 테이블에 원문만 upsert합니다.
    """,
) as dag:
    ingest_bills = PythonOperator(
        task_id="ingest_bills_from_api",
        python_callable=ingest_bills_from_api,
    )
