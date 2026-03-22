# -*- coding: utf-8 -*-
from __future__ import annotations

import sys

import pendulum

from airflow.models.dag import DAG
from airflow.models.param import Param
from airflow.operators.python import PythonOperator


def poll_and_ingest_batch_results(**context):
    params = context.get("params", {})
    max_jobs = int(params.get("max_jobs") or 20)
    mode = params.get("execution_mode") or "dry_run"

    print(f"[batch-ingest] Current Mode: {mode}")

    project_root = "/opt/airflow/project"
    if project_root not in sys.path:
        sys.path.append(project_root)

    from src.lawdigest_data_pipeline.ai_batch_pipeline_utils import (
        apply_batch_results,
        ensure_status_tables,
        fetch_jobs_for_polling,
        get_db_connection,
        openai_download_file_content,
        openai_get_batch,
        update_job_status,
    )

    conn = get_db_connection(mode=mode if mode == "prod" else "test")
    processed_jobs = 0
    total_success = 0
    total_failed = 0

    try:
        ensure_status_tables(conn)
        jobs = fetch_jobs_for_polling(conn, max_jobs=max_jobs)
        if not jobs:
            print("[batch-ingest] 처리할 진행 중 batch가 없습니다.")
            return {"jobs": 0, "success": 0, "failed": 0, "mode": mode}

        for job in jobs:
            processed_jobs += 1
            batch = openai_get_batch(job["batch_id"])
            status = (batch.get("status") or "UNKNOWN").upper()
            output_file_id = batch.get("output_file_id")
            error_file_id = batch.get("error_file_id")

            if mode == "dry_run":
                print(f"[batch-ingest] [DRY_RUN] job_id={job['id']} status={status} (DB 업데이트 안 함)")
                continue

            update_job_status(
                conn=conn,
                job_id=job["id"],
                status=status,
                output_file_id=output_file_id,
                error_file_id=error_file_id,
                error_message=None,
            )

            if status != "COMPLETED" or not output_file_id:
                print(f"[batch-ingest] job_id={job['id']} status={status} (skip)")
                continue

            output_jsonl = openai_download_file_content(output_file_id)
            success, failed = apply_batch_results(conn, job_id=job["id"], output_jsonl=output_jsonl)
            total_success += success
            total_failed += failed

            final_status = "COMPLETED" if failed == 0 else "FAILED"
            update_job_status(
                conn=conn,
                job_id=job["id"],
                status=final_status,
                output_file_id=output_file_id,
                error_file_id=error_file_id,
                error_message=None if failed == 0 else f"{failed}건 처리 실패",
            )
            print(
                f"[batch-ingest] [{mode}] job_id={job['id']} batch_id={job['batch_id']} "
                f"success={success} failed={failed}"
            )

        return {"jobs": processed_jobs, "success": total_success, "failed": total_failed, "mode": mode}
    finally:
        conn.close()


with DAG(
    dag_id="lawdigest_ai_batch_ingest_dag",
    schedule="*/10 * * * *",
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    tags=["lawdigest", "ai-summary", "batch-ingest"],
    params={
        "execution_mode": Param(
            "dry_run",
            type="string",
            enum=["dry_run", "test", "prod"],
            title="실행 모드",
            description="dry_run: 상태 조회만 하고 DB 업데이트 안 함, test: 테스트 DB 사용, prod: 운영 DB 사용",
        ),
        "max_jobs": Param(20, type="integer", title="한 번에 조회할 batch 개수"),
    },
    doc_md="""
    ### Lawdigest AI Batch 결과 수신 DAG (테스트 DB)

    - 진행 중인 OpenAI Batch 작업 상태를 조회합니다.
    - 완료된 작업의 output 파일을 다운로드하여 Bill 테이블에 요약을 반영합니다.
    - 상태 테이블(ai_batch_jobs, ai_batch_items)을 갱신합니다.
    """,
) as dag:
    ingest_batch_results = PythonOperator(
        task_id="poll_and_ingest_batch_results",
        python_callable=poll_and_ingest_batch_results,
    )

