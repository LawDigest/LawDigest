from __future__ import annotations

from typing import Any, Dict

from lawdigest_ai.db import get_db_connection
from lawdigest_ai.processor.batch_utils import (
    apply_batch_results,
    fetch_jobs_for_polling,
    openai_download_file_content,
    openai_get_batch,
    update_job_status,
)


def ingest_batch_results(max_jobs: int = 10, mode: str = "dry_run") -> Dict[str, Any]:
    """완료된 OpenAI Batch 작업의 결과를 수집하여 DB에 적재합니다.

    Args:
        max_jobs: 한 번에 처리할 최대 작업 수
        mode: 'dry_run' | 'test' | 'prod'
    """
    conn = get_db_connection(mode=mode if mode == "prod" else "test")
    total_success = total_failed = 0
    try:
        jobs = fetch_jobs_for_polling(conn, max_jobs=max_jobs)
        if not jobs:
            print("[batch-ingest] 폴링 대상 작업이 없습니다.")
            return {"processed_jobs": 0, "mode": mode}

        for job in jobs:
            job_id = job["id"]
            batch_id = job["batch_id"]
            batch_obj = openai_get_batch(batch_id)
            status = (batch_obj.get("status") or "").upper()
            output_file_id = batch_obj.get("output_file_id")
            error_file_id = batch_obj.get("error_file_id")

            update_job_status(
                conn,
                job_id=job_id,
                status=status,
                output_file_id=output_file_id,
                error_file_id=error_file_id,
            )

            if status != "COMPLETED" or not output_file_id:
                print(f"[batch-ingest] batch_id={batch_id} status={status} - 아직 완료되지 않음")
                continue

            if mode == "dry_run":
                print(f"[batch-ingest] [DRY_RUN] batch_id={batch_id} COMPLETED - 결과 적재 생략")
                continue

            output_jsonl = openai_download_file_content(output_file_id)
            success, failed = apply_batch_results(conn, job_id=job_id, output_jsonl=output_jsonl)
            total_success += success
            total_failed += failed
            print(f"[batch-ingest] batch_id={batch_id} 적재 완료: 성공={success}, 실패={failed}")

    finally:
        conn.close()

    return {
        "processed_jobs": len(jobs),
        "total_success": total_success,
        "total_failed": total_failed,
        "mode": mode,
    }
