from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pymysql
import requests
from pydantic import BaseModel, ConfigDict, Field, ValidationError


OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
ACTIVE_BATCH_STATES = ("VALIDATING", "IN_PROGRESS", "FINALIZING", "SUBMITTED")


class BatchStructuredSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    brief_summary: str = Field(alias="briefSummary")
    gpt_summary: str = Field(alias="gptSummary")
    tags: List[str] = Field(alias="tags", min_length=5, max_length=5)


def _read_dotenv(path: str) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not os.path.exists(path):
        return values

    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            normalized = value.strip()
            if (normalized.startswith('"') and normalized.endswith('"')) or (
                normalized.startswith("'") and normalized.endswith("'")
            ):
                normalized = normalized[1:-1]
            values[key.strip()] = normalized

    return values


def get_test_db_config() -> Dict[str, Any]:
    env_file_values = _read_dotenv("/opt/airflow/project/.env")

    host = os.getenv("TEST_DB_HOST") or env_file_values.get("TEST_DB_HOST")
    port = os.getenv("TEST_DB_PORT") or env_file_values.get("TEST_DB_PORT")
    user = os.getenv("TEST_DB_USER") or env_file_values.get("TEST_DB_USER")
    password = os.getenv("TEST_DB_PASSWORD") or env_file_values.get("TEST_DB_PASSWORD")
    database = os.getenv("TEST_DB_NAME") or env_file_values.get("TEST_DB_NAME")

    if not all([host, port, user, password, database]):
        missing = [
            key
            for key, value in {
                "TEST_DB_HOST": host,
                "TEST_DB_PORT": port,
                "TEST_DB_USER": user,
                "TEST_DB_PASSWORD": password,
                "TEST_DB_NAME": database,
            }.items()
            if not value
        ]
        raise ValueError(f"테스트 DB 환경변수가 누락되었습니다: {', '.join(missing)}")

    return {
        "host": host,
        "port": int(port),
        "user": user,
        "password": password,
        "database": database,
    }


def get_prod_db_config() -> Dict[str, Any]:
    """
    운영 DB 환경 설정을 반환합니다.
    """
    env_file_values = _read_dotenv("/opt/airflow/project/.env")

    host = os.getenv("DB_HOST") or env_file_values.get("DB_HOST")
    port = os.getenv("DB_PORT") or env_file_values.get("DB_PORT")
    user = os.getenv("DB_USER") or env_file_values.get("DB_USER")
    password = os.getenv("DB_PASSWORD") or env_file_values.get("DB_PASSWORD")
    database = os.getenv("DB_NAME") or env_file_values.get("DB_NAME")

    if not all([host, port, user, password, database]):
        missing = [
            key
            for key, value in {
                "DB_HOST": host,
                "DB_PORT": port,
                "DB_USER": user,
                "DB_PASSWORD": password,
                "DB_NAME": database,
            }.items()
            if not value
        ]
        raise ValueError(f"운영 DB 환경변수가 누락되었습니다: {', '.join(missing)}")

    return {
        "host": host,
        "port": int(port),
        "user": user,
        "password": password,
        "database": database,
    }


def get_openai_api_key() -> str:
    key = os.getenv("OPENAI_API_KEY") or os.getenv("APIKEY_OPENAI")
    if not key:
        raise ValueError("OPENAI_API_KEY 또는 APIKEY_OPENAI가 설정되어야 합니다.")
    return key


def get_db_connection(mode: str = "test") -> pymysql.connections.Connection:
    """
    지정된 모드(prod/test)에 따른 DB 연결 객체를 반환합니다.
    """
    if mode == "prod":
        cfg = get_prod_db_config()
    else:
        cfg = get_test_db_config()

    return pymysql.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        db=cfg["database"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


def ensure_status_tables(conn: pymysql.connections.Connection) -> None:
    ddl = [
        """
        CREATE TABLE IF NOT EXISTS ai_batch_jobs (
          id BIGINT AUTO_INCREMENT PRIMARY KEY,
          batch_id VARCHAR(128) NOT NULL UNIQUE,
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
          INDEX idx_ai_batch_jobs_status (status),
          INDEX idx_ai_batch_jobs_created_at (created_at)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS ai_batch_items (
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
          CONSTRAINT fk_ai_batch_items_job
            FOREIGN KEY (job_id) REFERENCES ai_batch_jobs(id)
            ON DELETE CASCADE
        )
        """,
    ]

    with conn.cursor() as cursor:
        for stmt in ddl:
            cursor.execute(stmt)
    conn.commit()


def fetch_unsummarized_bills(
    conn: pymysql.connections.Connection,
    limit: int,
) -> List[Dict[str, Any]]:
    sql = f"""
    SELECT
      b.bill_id,
      b.bill_name,
      b.summary,
      b.proposers,
      b.proposer_kind,
      b.propose_date,
      b.stage
    FROM Bill b
    WHERE b.summary IS NOT NULL
      AND b.summary <> ''
      AND (b.brief_summary IS NULL OR b.brief_summary = '' OR b.gpt_summary IS NULL OR b.gpt_summary = '')
      AND NOT EXISTS (
        SELECT 1
        FROM ai_batch_items i
        JOIN ai_batch_jobs j ON j.id = i.job_id
        WHERE i.bill_id = b.bill_id
          AND j.status IN ({",".join(["%s"] * len(ACTIVE_BATCH_STATES))})
      )
    ORDER BY b.propose_date DESC
    LIMIT %s
    """
    params = list(ACTIVE_BATCH_STATES) + [limit]
    with conn.cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchall()


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


def build_batch_request_rows(
    bills: List[Dict[str, Any]],
    model: str,
) -> List[Dict[str, Any]]:
    summary_schema = BatchStructuredSummary.model_json_schema(by_alias=True)
    rows: List[Dict[str, Any]] = []
    for bill in bills:
        bill_id = bill["bill_id"]
        rows.append(
            {
                "custom_id": bill_id,
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "당신은 한국 법안 요약 전문가입니다. 반드시 JSON 객체로만 응답하세요.",
                        },
                        {
                            "role": "user",
                            "content": _build_prompt_for_bill(bill),
                        },
                    ],
                    "temperature": 0.2,
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "bill_summary",
                            "strict": True,
                            "schema": summary_schema,
                        },
                    },
                },
            }
        )
    return rows


def write_jsonl_tempfile(rows: List[Dict[str, Any]]) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as tmp:
        for row in rows:
            tmp.write(json.dumps(row, ensure_ascii=False) + "\n")
        return tmp.name


def _headers() -> Dict[str, str]:
    return {"Authorization": f"Bearer {get_openai_api_key()}"}


def openai_upload_batch_file(jsonl_path: str) -> str:
    with open(jsonl_path, "rb") as f:
        resp = requests.post(
            f"{OPENAI_BASE_URL}/files",
            headers=_headers(),
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
        f"{OPENAI_BASE_URL}/files/{file_id}/content",
        headers=_headers(),
        timeout=120,
    )
    resp.raise_for_status()
    return resp.text


def create_batch_job_with_items(
    conn: pymysql.connections.Connection,
    batch_id: str,
    input_file_id: str,
    model: str,
    bill_ids: List[str],
    status: str = "SUBMITTED",
) -> int:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO ai_batch_jobs (
              batch_id, status, input_file_id, endpoint, model_name, total_count, submitted_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                batch_id,
                status,
                input_file_id,
                "/v1/chat/completions",
                model,
                len(bill_ids),
                datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        job_id = cursor.lastrowid
        item_rows = [(job_id, bill_id, bill_id, "SUBMITTED") for bill_id in bill_ids]
        cursor.executemany(
            """
            INSERT INTO ai_batch_items (job_id, bill_id, custom_id, status)
            VALUES (%s, %s, %s, %s)
            """,
            item_rows,
        )
    conn.commit()
    return int(job_id)


def fetch_jobs_for_polling(
    conn: pymysql.connections.Connection,
    max_jobs: int,
) -> List[Dict[str, Any]]:
    sql = """
    SELECT *
    FROM ai_batch_jobs
    WHERE status IN ('SUBMITTED', 'VALIDATING', 'IN_PROGRESS', 'FINALIZING')
    ORDER BY created_at ASC
    LIMIT %s
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (max_jobs,))
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
            """
            UPDATE ai_batch_jobs
            SET status=%s,
                output_file_id=%s,
                error_file_id=%s,
                error_message=%s,
                completed_at=CASE WHEN %s IN ('COMPLETED','FAILED','CANCELED','EXPIRED')
                                  THEN NOW() ELSE completed_at END
            WHERE id=%s
            """,
            (
                status,
                output_file_id,
                error_file_id,
                error_message,
                status,
                job_id,
            ),
        )
    conn.commit()


def _extract_message_content(choice_message: Any) -> str:
    if isinstance(choice_message, str):
        return choice_message
    if isinstance(choice_message, list):
        parts: List[str] = []
        for item in choice_message:
            if isinstance(item, dict):
                text = item.get("text")
                if text:
                    parts.append(text)
        return "".join(parts)
    if isinstance(choice_message, dict):
        content = choice_message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return _extract_message_content(content)
    return ""


def parse_output_jsonl_line(
    line: str,
) -> Tuple[str, Optional[str], Optional[str], Optional[List[str]], Optional[str]]:
    """
    Returns: (bill_id, brief_summary, gpt_summary, tags, error_message)
    """
    row = json.loads(line)
    bill_id = row.get("custom_id")
    response = row.get("response") or {}
    status_code = response.get("status_code")
    if status_code != 200:
        return bill_id, None, None, None, f"batch response status_code={status_code}"

    body = response.get("body") or {}
    choices = body.get("choices") or []
    if not choices:
        return bill_id, None, None, None, "choices가 비어있습니다."

    message = choices[0].get("message", {})
    content = _extract_message_content(message.get("content", ""))
    if not content:
        return bill_id, None, None, None, "message content가 비어있습니다."

    try:
        parsed = BatchStructuredSummary.model_validate_json(content)
    except ValidationError as exc:
        return bill_id, None, None, None, f"요약 Structured Output 검증 실패: {exc}"

    return bill_id, parsed.brief_summary, parsed.gpt_summary, parsed.tags, None


def apply_batch_results(
    conn: pymysql.connections.Connection,
    job_id: int,
    output_jsonl: str,
) -> Tuple[int, int]:
    success = 0
    failed = 0
    with conn.cursor() as cursor:
        lines = [line for line in output_jsonl.splitlines() if line.strip()]
        for line in lines:
            bill_id, brief, gpt, tags, err = parse_output_jsonl_line(line)
            if not bill_id:
                failed += 1
                continue

            if err:
                failed += 1
                cursor.execute(
                    """
                    UPDATE ai_batch_items
                    SET status='FAILED',
                        retry_count=retry_count+1,
                        error_message=%s,
                        processed_at=NOW()
                    WHERE job_id=%s AND bill_id=%s
                    """,
                    (err, job_id, bill_id),
                )
                continue

            cursor.execute(
                """
                UPDATE Bill
                SET brief_summary=%s,
                    gpt_summary=%s,
                    summary_tags=%s,
                    modified_date=NOW()
                WHERE bill_id=%s
                """,
                (brief, gpt, json.dumps(tags or [], ensure_ascii=False), bill_id),
            )
            cursor.execute(
                """
                UPDATE ai_batch_items
                SET status='DONE',
                    error_message=NULL,
                    processed_at=NOW()
                WHERE job_id=%s AND bill_id=%s
                """,
                (job_id, bill_id),
            )
            success += 1

        cursor.execute(
            """
            UPDATE ai_batch_items
            SET status='FAILED',
                retry_count=retry_count+1,
                error_message=COALESCE(error_message, 'output에 결과가 없습니다.'),
                processed_at=NOW()
            WHERE job_id=%s
              AND status='SUBMITTED'
            """,
            (job_id,),
        )
        failed += cursor.rowcount

        cursor.execute(
            """
            UPDATE ai_batch_jobs
            SET success_count=%s,
                failed_count=%s
            WHERE id=%s
            """,
            (success, failed, job_id),
        )
    conn.commit()
    return success, failed
