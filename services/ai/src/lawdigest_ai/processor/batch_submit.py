from __future__ import annotations

import os
from typing import Any, Dict

from lawdigest_ai.db import get_db_connection
from lawdigest_ai.processor.batch_utils import (
    build_batch_request_rows,
    create_batch_job_with_items,
    ensure_status_tables,
    fetch_unsummarized_bills,
    openai_create_batch,
    openai_upload_batch_file,
    write_jsonl_tempfile,
)


def submit_batch(limit: int = 200, model: str = "gpt-4o-mini", mode: str = "dry_run") -> Dict[str, Any]:
    """미요약 법안을 OpenAI Batch API에 제출합니다.

    Args:
        limit: 한 번에 처리할 최대 법안 수
        model: 사용할 OpenAI 모델명
        mode: 'dry_run' | 'test' | 'prod'
    """
    conn = get_db_connection(mode=mode if mode == "prod" else "test")
    try:
        ensure_status_tables(conn)
        bills = fetch_unsummarized_bills(conn, limit=limit)
        if not bills:
            print("[batch-submit] 제출 대상 법안이 없습니다.")
            return {"submitted": 0, "mode": mode}

        if mode == "dry_run":
            print(f"[batch-submit] [DRY_RUN] {len(bills)}개 법안 제출 대상 선정. (실제 제출 안 함)")
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
