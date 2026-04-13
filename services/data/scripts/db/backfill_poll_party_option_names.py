from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from lawdigest_data.connectors.DatabaseManager import DatabaseManager

PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_SRC = PROJECT_ROOT / "services" / "data" / "src"
AI_SRC = PROJECT_ROOT / "services" / "ai" / "src"

for path in (str(DATA_SRC), str(AI_SRC)):
    if path not in sys.path:
        sys.path.insert(0, path)

def build_backfill_updates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from lawdigest_data.polls.normalization import normalize_party_name

    return [
        {
            "option_id": row["option_id"],
            "before": row["option_name"],
            "after": normalize_party_name(row["option_name"]),
        }
        for row in rows
        if normalize_party_name(row["option_name"]) != row["option_name"]
    ]


def summarize_updates(updates: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "update_count": len(updates),
        "before_counts": dict(Counter(update["before"] for update in updates)),
        "after_counts": dict(Counter(update["after"] for update in updates)),
    }


def _resolve_db_config(mode: str) -> dict[str, Any]:
    from lawdigest_ai.db import get_prod_db_config, get_test_db_config

    if mode == "prod":
        return get_prod_db_config()

    try:
        return get_test_db_config()
    except ValueError:
        return {
            "host": os.environ.get("TEST_DB_HOST", "140.245.74.246"),
            "port": int(os.environ.get("TEST_DB_PORT", "2812")),
            "user": os.environ.get("TEST_DB_USER", "root"),
            "password": os.environ.get("TEST_DB_PASSWORD", "eLL-@hjm3K7CgFDV-MKp"),
            "database": os.environ.get("TEST_DB_NAME", "lawTestDB"),
        }


def _build_db_manager(mode: str) -> DatabaseManager:
    from lawdigest_data.connectors.DatabaseManager import DatabaseManager

    db_config = _resolve_db_config(mode)
    return DatabaseManager(
        host=db_config["host"],
        port=db_config["port"],
        username=db_config["user"],
        password=db_config["password"],
        database=db_config["database"],
    )


def _load_candidate_rows(db_manager) -> list[dict[str, Any]]:
    query = """
        SELECT option_id, option_name
        FROM PollOption
        WHERE option_name IS NOT NULL
          AND TRIM(option_name) <> ''
        ORDER BY option_id ASC
    """
    return db_manager.execute_query(query) or []


def _apply_updates(db_manager, updates: list[dict[str, Any]]) -> int:
    if not updates:
        return 0

    query = """
        UPDATE PollOption
        SET option_name = %s,
            modified_date = NOW()
        WHERE option_id = %s
    """
    params = [(update["after"], update["option_id"]) for update in updates]
    db_manager.execute_batch(query, params)
    return len(params)


def run_backfill(mode: str, apply: bool, limit: int | None = None) -> dict[str, Any]:
    from lawdigest_data.core.WorkFlowManager import WorkFlowManager

    normalized_mode = WorkFlowManager.normalize_execution_mode(mode)
    db_manager = _build_db_manager(normalized_mode)

    candidate_rows = _load_candidate_rows(db_manager)
    updates = build_backfill_updates(candidate_rows)
    if limit and limit > 0:
        updates = updates[:limit]

    summary = {
        "mode": normalized_mode,
        "apply": apply,
        **summarize_updates(updates),
        "sample": updates[:20],
    }

    if apply:
        summary["applied_count"] = _apply_updates(db_manager, updates)
    else:
        summary["applied_count"] = 0

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="PollOption 정당명 공백 변형 백필")
    parser.add_argument(
        "--mode",
        default="test",
        choices=["dry_run", "test", "test_db", "prod"],
        help="DB 실행 모드",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="실제 DB 업데이트 수행",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="처리 대상 제한 수 (0이면 전체)",
    )
    args = parser.parse_args()

    summary = run_backfill(
        mode=args.mode,
        apply=args.apply,
        limit=args.limit or None,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
