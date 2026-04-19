from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pymysql
import requests
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from lawdigest_ai.config import get_openai_api_key, OPENAI_BASE_URL

ACTIVE_BATCH_STATES = ("VALIDATING", "IN_PROGRESS", "FINALIZING", "SUBMITTED")


class BatchStructuredSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")
    brief_summary: str = Field(alias="briefSummary")
    gpt_summary: str = Field(alias="gptSummary")
    tags: List[str] = Field(alias="tags", min_length=5, max_length=5)


def _headers() -> Dict[str, str]:
    return {"Authorization": f"Bearer {get_openai_api_key()}"}


def _build_prompt_for_bill(row: Dict[str, Any]) -> str:
    payload = {
        "bill_id": row.get("bill_id"),
        "bill_name": row.get("bill_name"),
        "proposers": row.get("proposers"),
        "proposer_kind": row.get("proposer_kind"),
        "propose_date": str(row.get("propose_date") or ""),
        "stage": row.get("stage"),
        "summary": row.get("summary"),
    }
    return (
        "다음 법안 정보를 보고 JSON으로만 응답하세요.\n"
        "키는 briefSummary, gptSummary, tags 세 개만 포함해야 합니다.\n"
        "briefSummary는 1문장 요약, gptSummary는 3~7개 핵심 항목 중심 상세 요약입니다.\n"
        "tags는 중복 없는 한국어 태그 정확히 5개입니다.\n\n"
        f"{json.dumps(payload, ensure_ascii=False)}"
    )


def build_batch_request_rows(bills: List[Dict[str, Any]], model: str) -> List[Dict[str, Any]]:
    summary_schema = BatchStructuredSummary.model_json_schema(by_alias=True)
    return [
        {
            "custom_id": bill["bill_id"],
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": model,
                "messages": [
                    {"role": "system", "content": "당신은 한국 법안 요약 전문가입니다. 반드시 JSON 객체로만 응답하세요."},
                    {"role": "user", "content": _build_prompt_for_bill(bill)},
                ],
                "temperature": 0.2,
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {"name": "bill_summary", "strict": True, "schema": summary_schema},
                },
            },
        }
        for bill in bills
    ]


def write_jsonl_tempfile(rows: List[Dict[str, Any]]) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as tmp:
        for row in rows:
            tmp.write(json.dumps(row, ensure_ascii=False) + "\n")
        return tmp.name


def openai_upload_batch_file(jsonl_path: str) -> str:
    with open(jsonl_path, "rb") as f:
        resp = requests.post(
            f"{OPENAI_BASE_URL}/files", headers=_headers(),
            data={"purpose": "batch"},
            files={"file": (os.path.basename(jsonl_path), f, "application/jsonl")},
            timeout=60,
        )
    resp.raise_for_status()
    return resp.json()["id"]


def openai_create_batch(input_file_id: str, model: str) -> Dict[str, Any]:
    payload = {
        "input_file_id": input_file_id,
        "endpoint": "/v1/chat/completions",
        "completion_window": "24h",
        "metadata": {"model": model, "pipeline": "lawdigest_ai_batch"},
    }
    resp = requests.post(
        f"{OPENAI_BASE_URL}/batches",
        headers={**_headers(), "Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def openai_get_batch(batch_id: str) -> Dict[str, Any]:
    resp = requests.get(f"{OPENAI_BASE_URL}/batches/{batch_id}", headers=_headers(), timeout=60)
    resp.raise_for_status()
    return resp.json()


def openai_download_file_content(file_id: str) -> str:
    resp = requests.get(
        f"{OPENAI_BASE_URL}/files/{file_id}/content", headers=_headers(), timeout=120
    )
    resp.raise_for_status()
    return resp.text


def _extract_message_content(choice_message: Any) -> str:
    if isinstance(choice_message, str):
        return choice_message
    if isinstance(choice_message, list):
        return "".join(item.get("text", "") for item in choice_message if isinstance(item, dict))
    if isinstance(choice_message, dict):
        content = choice_message.get("content")
        return _extract_message_content(content) if content else ""
    return ""


def parse_output_jsonl_line(
    line: str,
) -> Tuple[str, Optional[str], Optional[str], Optional[List[str]], Optional[str]]:
    row = json.loads(line)
    bill_id = row.get("custom_id")
    response = row.get("response") or {}
    if response.get("status_code") != 200:
        return bill_id, None, None, None, f"status_code={response.get('status_code')}"
    choices = (response.get("body") or {}).get("choices") or []
    if not choices:
        return bill_id, None, None, None, "choices가 비어있습니다."
    content = _extract_message_content(choices[0].get("message", {}).get("content", ""))
    if not content:
        return bill_id, None, None, None, "message content가 비어있습니다."
    try:
        parsed = BatchStructuredSummary.model_validate_json(content)
    except ValidationError as exc:
        return bill_id, None, None, None, f"Structured Output 검증 실패: {exc}"
    return bill_id, parsed.brief_summary, parsed.gpt_summary, parsed.tags, None


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
) -> int:
    with conn.cursor() as cursor:
        cursor.execute(
            """INSERT INTO ai_batch_jobs (provider, batch_id, status, input_file_id, endpoint, model_name, total_count, submitted_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                provider, batch_id, status, input_file_id, "/v1/chat/completions", model,
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
            "SELECT * FROM ai_batch_jobs WHERE status IN ('SUBMITTED','VALIDATING','IN_PROGRESS','FINALIZING') "
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
        for line in [raw_line for raw_line in output_jsonl.splitlines() if raw_line.strip()]:
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
