from __future__ import annotations
import os
from typing import Any, Dict
import pymysql
from dotenv import load_dotenv, dotenv_values

load_dotenv()

_ENV_DOTENV_PATH = os.getenv("AIRFLOW_DOTENV_PATH", "/opt/airflow/project/.env")


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
