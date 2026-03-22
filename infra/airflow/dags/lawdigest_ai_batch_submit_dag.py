# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import sys

import pendulum

from airflow.models.dag import DAG
from airflow.models.param import Param
from airflow.operators.python import PythonOperator


def submit_ai_batch(**context):
    params = context.get("params", {})
    limit = int(params.get("limit") or 200)
    model = params.get("model") or "gpt-4o-mini"
    mode = params.get("execution_mode") or "dry_run"

    print(f"[batch-submit] Current Mode: {mode}")

    project_root = "/opt/airflow/project"
    if project_root not in sys.path:
        sys.path.append(project_root)

    from src.lawdigest_data_pipeline.ai_batch_pipeline_utils import (
        build_batch_request_rows,
        create_batch_job_with_items,
        ensure_status_tables,
        fetch_unsummarized_bills,
        get_db_connection,
        openai_create_batch,
        openai_upload_batch_file,
        write_jsonl_tempfile,
    )

    conn = get_db_connection(mode=mode if mode == "prod" else "test")
    try:
        ensure_status_tables(conn)
        bills = fetch_unsummarized_bills(conn, limit=limit)
        if not bills:
            print("[batch-submit] 제출 대상 법안이 없습니다.")
            return {"submitted": 0, "mode": mode}

        if mode == "dry_run":
            print(f"[batch-submit] [DRY_RUN] {len(bills)}개의 법안을 요약 제출 대상으로 선정했습니다. (실제 제출 안 함)")
            return {"submitted": len(bills), "mode": "dry_run"}

        request_rows = build_batch_request_rows(bills, model=model)
        jsonl_path = write_jsonl_tempfile(request_rows)
        try:
            input_file_id = openai_upload_batch_file(jsonl_path)
            batch_obj = openai_create_batch(input_file_id=input_file_id, model=model)
            batch_id = batch_obj["id"]

            job_id = create_batch_job_with_items(
                conn=conn,
                batch_id=batch_id,
                input_file_id=input_file_id,
                model=model,
                bill_ids=[b["bill_id"] for b in bills],
                status=(batch_obj.get("status") or "SUBMITTED").upper(),
            )
            print(f"[batch-submit] [{mode}] job_id={job_id} batch_id={batch_id} count={len(bills)}")
            return {"submitted": len(bills), "batch_id": batch_id, "job_id": job_id, "mode": mode}
        finally:
            if os.path.exists(jsonl_path):
                os.remove(jsonl_path)
    finally:
        conn.close()


with DAG(
    dag_id="lawdigest_ai_batch_submit_dag",
    schedule="10 * * * *",
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    tags=["lawdigest", "ai-summary", "batch-submit"],
    params={
        "execution_mode": Param(
            "dry_run",
            type="string",
            enum=["dry_run", "test", "prod"],
            title="실행 모드",
            description="dry_run: 제출 없이 대상만 확인, test: 테스트 DB 사용, prod: 운영 DB 사용",
        ),
        "limit": Param(200, type="integer", title="배치 최대 건수"),
        "model": Param("gpt-4o-mini", type="string", title="모델명"),
    },
    doc_md="""
    ### Lawdigest AI Batch 제출 DAG (테스트 DB)

    - DB에서 미요약 법안을 조회해 OpenAI Batch 작업으로 제출합니다.
    - 상태 테이블(ai_batch_jobs, ai_batch_items)에 batch 상태를 기록합니다.
    """,
) as dag:
    submit_batch = PythonOperator(
        task_id="submit_ai_batch",
        python_callable=submit_ai_batch,
    )

