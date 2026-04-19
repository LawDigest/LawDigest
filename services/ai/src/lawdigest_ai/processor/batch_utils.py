from __future__ import annotations

import json
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pymysql

from lawdigest_ai.processor.providers.openai_batch import OpenAIBatchProvider
from lawdigest_ai.processor.providers.types import BatchProviderJobState

ACTIVE_BATCH_STATES = ("VALIDATING", "IN_PROGRESS", "FINALIZING", "SUBMITTED", "CANCELLING")


def build_batch_request_rows(bills: List[Dict[str, Any]], model: str) -> List[Dict[str, Any]]:
    return OpenAIBatchProvider().build_request_rows(bills, model)


def write_jsonl_tempfile(rows: List[Dict[str, Any]]) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as tmp:
        for row in rows:
            tmp.write(json.dumps(row, ensure_ascii=False) + "\n")
        return tmp.name


def openai_upload_batch_file(jsonl_path: str) -> str:
    return OpenAIBatchProvider().upload_batch_file(jsonl_path)


def openai_create_batch(input_file_id: str, model: str) -> Dict[str, Any]:
    state = OpenAIBatchProvider().create_batch_job(model=model, source_file_name=input_file_id)
    return _job_state_to_legacy_dict(state)


def openai_get_batch(batch_id: str) -> Dict[str, Any]:
    state = OpenAIBatchProvider().get_batch_job(batch_id)
    return _job_state_to_legacy_dict(state)


def openai_download_file_content(file_id: str) -> str:
    return OpenAIBatchProvider().download_output_file(file_id)


def parse_output_jsonl_line(
    line: str,
) -> Tuple[str, Optional[str], Optional[str], Optional[List[str]], Optional[str]]:
    result = OpenAIBatchProvider().parse_output_line(line)
    return result.bill_id, result.brief_summary, result.gpt_summary, result.tags, result.error


def _job_state_to_legacy_dict(state: BatchProviderJobState) -> Dict[str, Any]:
    return {
        "id": state.batch_id,
        "status": state.status.lower(),
        "output_file_id": state.output_file_id,
        "error_file_id": state.error_file_id,
        "error_message": state.error_message,
    }


def ensure_status_tables(conn: pymysql.connections.Connection) -> None:
    ddl = [
        """CREATE TABLE IF NOT EXISTS ai_batch_jobs (
          id BIGINT AUTO_INCREMENT PRIMARY KEY,
          provider VARCHAR(32) NOT NULL DEFAULT 'openai',
          batch_id VARCHAR(128) NOT NULL,
          status VARCHAR(32) NOT NULL,
          input_file_id VARCHAR(128) NULL,
          output_file_id VARCHAR(128) NULL,
          error_file_id VARCHAR(128) NULL,
          endpoint VARCHAR(64) NOT NULL DEFAULT '/v1/chat/completions',
          model_name VARCHAR(64) NOT NULL,
          total_count INT NOT NULL DEFAULT 0,
          success_count INT NOT NULL DEFAULT 0,
          failed_count INT NOT NULL DEFAULT 0,
          submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          completed_at DATETIME NULL,
          error_message TEXT NULL,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          UNIQUE KEY uq_ai_batch_jobs_provider_batch_id (provider, batch_id),
          INDEX idx_ai_batch_jobs_status (status),
          INDEX idx_ai_batch_jobs_created_at (created_at),
          INDEX idx_ai_batch_jobs_provider_status_created_at (provider, status, created_at)
        )""",
        """CREATE TABLE IF NOT EXISTS ai_batch_items (
          id BIGINT AUTO_INCREMENT PRIMARY KEY,
          job_id BIGINT NOT NULL,
          bill_id VARCHAR(100) NOT NULL,
          custom_id VARCHAR(150) NOT NULL,
          status VARCHAR(32) NOT NULL DEFAULT 'SUBMITTED',
          retry_count INT NOT NULL DEFAULT 0,
          error_message TEXT NULL,
          processed_at DATETIME NULL,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          UNIQUE KEY uq_ai_batch_items_job_bill (job_id, bill_id),
          INDEX idx_ai_batch_items_bill (bill_id),
          INDEX idx_ai_batch_items_status (status),
          CONSTRAINT fk_ai_batch_items_job FOREIGN KEY (job_id) REFERENCES ai_batch_jobs(id) ON DELETE CASCADE
        )""",
    ]
    with conn.cursor() as cursor:
        for stmt in ddl:
            cursor.execute(stmt)
    conn.commit()


def fetch_unsummarized_bills(conn: pymysql.connections.Connection, limit: int) -> List[Dict[str, Any]]:
    sql = f"""
    SELECT b.bill_id, b.bill_name, b.summary, b.proposers, b.proposer_kind, b.propose_date, b.stage
    FROM Bill b
    WHERE b.summary IS NOT NULL AND b.summary <> ''
      AND (b.brief_summary IS NULL OR b.brief_summary = '' OR b.gpt_summary IS NULL OR b.gpt_summary = '')
      AND NOT EXISTS (
        SELECT 1 FROM ai_batch_items i JOIN ai_batch_jobs j ON j.id = i.job_id
        WHERE i.bill_id = b.bill_id AND j.status IN ({",".join(["%s"] * len(ACTIVE_BATCH_STATES))})
      )
    ORDER BY b.propose_date DESC LIMIT %s
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, list(ACTIVE_BATCH_STATES) + [limit])
        return cursor.fetchall()


def create_batch_job_with_items(
    conn: pymysql.connections.Connection,
    batch_id: str,
    input_file_id: str,
    model: str,
    bill_ids: List[str],
    status: str = "SUBMITTED",
    provider: str = "openai",
    endpoint: str = "/v1/chat/completions",
) -> int:
    with conn.cursor() as cursor:
        cursor.execute(
            """INSERT INTO ai_batch_jobs (provider, batch_id, status, input_file_id, endpoint, model_name, total_count, submitted_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                provider, batch_id, status, input_file_id, endpoint, model,
                len(bill_ids), datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        job_id = cursor.lastrowid
        cursor.executemany(
            "INSERT INTO ai_batch_items (job_id, bill_id, custom_id, status) VALUES (%s, %s, %s, %s)",
            [(job_id, bid, bid, "SUBMITTED") for bid in bill_ids],
        )
    conn.commit()
    return int(job_id)


def fetch_jobs_for_polling(conn: pymysql.connections.Connection, max_jobs: int) -> List[Dict[str, Any]]:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM ai_batch_jobs WHERE status IN ('SUBMITTED','VALIDATING','IN_PROGRESS','FINALIZING','CANCELLING') "
            "ORDER BY created_at ASC LIMIT %s",
            (max_jobs,),
        )
        return cursor.fetchall()


def update_job_status(
    conn: pymysql.connections.Connection,
    job_id: int,
    status: str,
    output_file_id: Optional[str],
    error_file_id: Optional[str],
    error_message: Optional[str] = None,
) -> None:
    with conn.cursor() as cursor:
        cursor.execute(
            """UPDATE ai_batch_jobs SET status=%s, output_file_id=%s, error_file_id=%s, error_message=%s,
               completed_at=CASE WHEN %s IN ('COMPLETED','FAILED','CANCELED','EXPIRED') THEN NOW() ELSE completed_at END
               WHERE id=%s""",
            (status, output_file_id, error_file_id, error_message, status, job_id),
        )
    conn.commit()


def apply_batch_results(
    conn: pymysql.connections.Connection,
    job_id: int,
    output_jsonl: str,
) -> Tuple[int, int]:
    success = failed = 0
    with conn.cursor() as cursor:
        for line in [l for l in output_jsonl.splitlines() if l.strip()]:  # noqa: E741
            bill_id, brief, gpt, tags, err = parse_output_jsonl_line(line)
            if not bill_id:
                failed += 1
                continue
            if err:
                failed += 1
                cursor.execute(
                    "UPDATE ai_batch_items SET status='FAILED', retry_count=retry_count+1, "
                    "error_message=%s, processed_at=NOW() WHERE job_id=%s AND bill_id=%s",
                    (err, job_id, bill_id),
                )
                continue
            cursor.execute(
                "UPDATE Bill SET brief_summary=%s, gpt_summary=%s, summary_tags=%s, modified_date=NOW() "
                "WHERE bill_id=%s",
                (brief, gpt, json.dumps(tags or [], ensure_ascii=False), bill_id),
            )
            cursor.execute(
                "UPDATE ai_batch_items SET status='DONE', error_message=NULL, processed_at=NOW() "
                "WHERE job_id=%s AND bill_id=%s",
                (job_id, bill_id),
            )
            success += 1

        cursor.execute(
            "UPDATE ai_batch_items SET status='FAILED', retry_count=retry_count+1, "
            "error_message=COALESCE(error_message, 'output에 결과가 없습니다.'), processed_at=NOW() "
            "WHERE job_id=%s AND status='SUBMITTED'",
            (job_id,),
        )
        failed += cursor.rowcount

        cursor.execute(
            "UPDATE ai_batch_jobs SET success_count=%s, failed_count=%s WHERE id=%s",
            (success, failed, job_id),
        )
    conn.commit()
    return success, failed
