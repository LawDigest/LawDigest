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
    *주의: 수집된 법안은 원문 그대로 저장되며, AI 요약은 `lawdigest_ai_summary_batch_dag` 등에 의해 별도로 수행됩니다.*
    """,
) as dag:
    ingest_bills = PythonOperator(
        task_id="ingest_bills_from_api",
        python_callable=ingest_bills_from_api,
    )
