from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any, Dict
import pymysql
from dotenv import load_dotenv, dotenv_values

_AIRFLOW_DOTENV_PATH = os.getenv("AIRFLOW_DOTENV_PATH")
_DEFAULT_AIRFLOW_DOTENV_PATH = str(
    Path(__file__).resolve().parents[4] / "services" / "data" / ".env",
)
_ENV_DOTENV_PATH = _AIRFLOW_DOTENV_PATH or _DEFAULT_AIRFLOW_DOTENV_PATH
load_dotenv(dotenv_path=_ENV_DOTENV_PATH)


def _get_db_config(prefix: str = "") -> Dict[str, Any]:
    """공통 DB 설정 조회 함수. prefix로 TEST_ 등 구분."""
    file_env = dotenv_values(_ENV_DOTENV_PATH)

    def _get(key: str) -> str | None:
        return os.getenv(key) or file_env.get(key)

    host = _get(f"{prefix}DB_HOST")
    port_str = _get(f"{prefix}DB_PORT")
    user = _get(f"{prefix}DB_USER")
    password = _get(f"{prefix}DB_PASSWORD")
    database = _get(f"{prefix}DB_NAME")

    missing = [k for k, v in {
        f"{prefix}DB_HOST": host,
        f"{prefix}DB_PORT": port_str,
        f"{prefix}DB_USER": user,
        f"{prefix}DB_PASSWORD": password,
        f"{prefix}DB_NAME": database,
    }.items() if not v]

    if missing:
        raise ValueError(f"DB 환경변수 누락: {', '.join(missing)}")

    assert port_str is not None  # missing 체크 이후 안전
    return {
        "host": host,
        "port": int(port_str),
        "user": user,
        "password": password,
        "database": database,
    }


def get_prod_db_config() -> Dict[str, Any]:
    """운영 DB 환경 설정을 반환합니다."""
    return _get_db_config(prefix="")


def get_test_db_config() -> Dict[str, Any]:
    """테스트 DB 환경 설정을 반환합니다."""
    return _get_db_config(prefix="TEST_")


def get_db_connection(mode: str = "test") -> pymysql.connections.Connection:
    """지정된 모드에 따른 DB 연결 객체를 반환합니다."""
    cfg = get_prod_db_config() if mode == "prod" else get_test_db_config()
    return pymysql.connect(
        host=cfg["host"], port=cfg["port"], user=cfg["user"],
        password=cfg["password"], db=cfg["database"],
        charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


def update_bill_summary(
    bill_id: str,
    brief_summary: str | None,
    gpt_summary: str | None,
    summary_tags: str | None,
    mode: str = "test",
) -> None:
    """Bill 테이블의 AI 요약을 업데이트하고 태그를 별도 테이블에 저장합니다."""
    conn = get_db_connection(mode=mode)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE Bill SET brief_summary=%s, gpt_summary=%s, modified_date=NOW() WHERE bill_id=%s",
                (brief_summary, gpt_summary, bill_id),
            )
            replace_bill_summary_tags(cur, bill_id, summary_tags)
        conn.commit()
    finally:
        conn.close()


def normalize_summary_tags(summary_tags: Any) -> list[str]:
    if summary_tags is None:
        return []
    if isinstance(summary_tags, str):
        value = summary_tags.strip()
        if not value:
            return []
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            parsed = [value]
    else:
        parsed = summary_tags

    if isinstance(parsed, (list, tuple, set)):
        values = parsed
    else:
        values = [parsed]

    normalized: list[str] = []
    seen: set[str] = set()
    for tag in values:
        text = str(tag).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        normalized.append(text)
    return normalized


def replace_bill_summary_tags(cursor: pymysql.cursors.Cursor, bill_id: str, summary_tags: Any) -> None:
    tags = normalize_summary_tags(summary_tags)
    cursor.execute("DELETE FROM BillSummaryTag WHERE bill_id=%s", (bill_id,))
    if not tags:
        return
    cursor.executemany(
        """
        INSERT INTO BillSummaryTag (bill_id, tag, created_date, modified_date)
        VALUES (%s, %s, NOW(), NOW())
        ON DUPLICATE KEY UPDATE modified_date=NOW()
        """,
        [(bill_id, tag) for tag in tags],
    )
