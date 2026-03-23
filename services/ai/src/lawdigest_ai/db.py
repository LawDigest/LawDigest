from __future__ import annotations
import os
from typing import Any, Dict
import pymysql
from dotenv import load_dotenv

load_dotenv()

_ENV_DOTENV_PATH = "/opt/airflow/project/.env"


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
            normalized = value.strip().strip("\"'")
            values[key.strip()] = normalized
    return values


def get_prod_db_config() -> Dict[str, Any]:
    env = _read_dotenv(_ENV_DOTENV_PATH)
    host = os.getenv("DB_HOST") or env.get("DB_HOST")
    port = os.getenv("DB_PORT") or env.get("DB_PORT")
    user = os.getenv("DB_USER") or env.get("DB_USER")
    password = os.getenv("DB_PASSWORD") or env.get("DB_PASSWORD")
    database = os.getenv("DB_NAME") or env.get("DB_NAME")
    missing = [k for k, v in {"DB_HOST": host, "DB_PORT": port, "DB_USER": user,
                               "DB_PASSWORD": password, "DB_NAME": database}.items() if not v]
    if missing:
        raise ValueError(f"운영 DB 환경변수 누락: {', '.join(missing)}")
    return {"host": host, "port": int(port), "user": user, "password": password, "database": database}


def get_test_db_config() -> Dict[str, Any]:
    env = _read_dotenv(_ENV_DOTENV_PATH)
    host = os.getenv("TEST_DB_HOST") or env.get("TEST_DB_HOST")
    port = os.getenv("TEST_DB_PORT") or env.get("TEST_DB_PORT")
    user = os.getenv("TEST_DB_USER") or env.get("TEST_DB_USER")
    password = os.getenv("TEST_DB_PASSWORD") or env.get("TEST_DB_PASSWORD")
    database = os.getenv("TEST_DB_NAME") or env.get("TEST_DB_NAME")
    missing = [k for k, v in {"TEST_DB_HOST": host, "TEST_DB_PORT": port, "TEST_DB_USER": user,
                               "TEST_DB_PASSWORD": password, "TEST_DB_NAME": database}.items() if not v]
    if missing:
        raise ValueError(f"테스트 DB 환경변수 누락: {', '.join(missing)}")
    return {"host": host, "port": int(port), "user": user, "password": password, "database": database}


def get_db_connection(mode: str = "test") -> pymysql.connections.Connection:
    cfg = get_prod_db_config() if mode == "prod" else get_test_db_config()
    return pymysql.connect(
        host=cfg["host"], port=cfg["port"], user=cfg["user"],
        password=cfg["password"], db=cfg["database"],
        charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )
