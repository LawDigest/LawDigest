from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from lawdigest_ai.db import get_db_connection, update_bill_summary
from lawdigest_ai.processor.gemini_cli_summarizer import GeminiCliSummarizer


DEFAULT_OUTPUT_PATH = "/tmp/gemini_ai_summary_results.json"


def _write_json_output(payload: Dict[str, Any], output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _db_mode_for_execution(mode: str) -> str:
    return "prod" if mode == "prod" else "test"


def _resolve_read_mode(mode: str, read_mode: str | None) -> str:
    if read_mode in {"test", "prod"}:
        return read_mode
    return _db_mode_for_execution(mode)


def _fetch_missing_bills(mode: str, limit: int, read_mode: str | None = None) -> List[Dict[str, Any]]:
    query = """
    SELECT
        bill_id,
        bill_name,
        summary,
        proposers,
        proposer_kind,
        brief_summary,
        gpt_summary,
        propose_date,
        stage
    FROM Bill
    WHERE
        (gpt_summary IS NULL OR gpt_summary = '' OR brief_summary IS NULL OR brief_summary = '')
        AND summary IS NOT NULL
        AND summary != ''
    ORDER BY propose_date DESC
    LIMIT %s
    """

    conn = get_db_connection(mode=_resolve_read_mode(mode, read_mode))
    try:
        with conn.cursor() as cur:
            cur.execute(query, (limit,))
            return list(cur.fetchall())
    finally:
        conn.close()


def _fetch_latest_bills(mode: str, limit: int, read_mode: str | None = None) -> List[Dict[str, Any]]:
    query = """
    SELECT
        bill_id,
        bill_name,
        summary,
        proposers,
        proposer_kind,
        brief_summary,
        gpt_summary,
        propose_date,
        stage
    FROM Bill
    WHERE
        summary IS NOT NULL
        AND summary != ''
    ORDER BY propose_date DESC
    LIMIT %s
    """

    conn = get_db_connection(mode=_resolve_read_mode(mode, read_mode))
    try:
        with conn.cursor() as cur:
            cur.execute(query, (limit,))
            return list(cur.fetchall())
    finally:
        conn.close()


def _normalize_item(row: Dict[str, Any], failure_map: Dict[str, str]) -> Dict[str, Any]:
    ai_title = row.get("brief_summary")
    ai_summary = row.get("gpt_summary")
    bill_id = row.get("bill_id")
    error = failure_map.get(str(bill_id))

    if not error and (not ai_title or not ai_summary):
        error = "Gemini 요약 결과에 필수 필드가 비어 있습니다."

    return {
        "bill_id": bill_id,
        "bill_name": row.get("bill_name"),
        "ai_title": ai_title,
        "ai_summary": ai_summary,
        "summary_tags": row.get("summary_tags"),
        "status": "failed" if error else "success",
        "error": error,
    }


def _upsert_successful_items(items: List[Dict[str, Any]], mode: str) -> int:
    upserted = 0
    for item in items:
        if item["status"] != "success":
            continue
        update_bill_summary(
            bill_id=str(item["bill_id"]),
            brief_summary=item.get("ai_title"),
            gpt_summary=item.get("ai_summary"),
            summary_tags=item.get("summary_tags"),
            mode=_db_mode_for_execution(mode),
        )
        upserted += 1
    return upserted


def run_gemini_repair_pipeline(
    mode: str = "dry_run",
    limit: int = 20,
    batch_size: int = 5,
    output_path: str = DEFAULT_OUTPUT_PATH,
    stop_on_error: bool = False,
    read_mode: str | None = None,
    target_mode: str = "missing",
) -> Dict[str, Any]:
    if limit < 1:
        raise ValueError("limit는 1 이상이어야 합니다.")
    if batch_size < 1:
        raise ValueError("batch_size는 1 이상이어야 합니다.")
    if target_mode not in {"missing", "latest"}:
        raise ValueError("target_mode는 missing 또는 latest 여야 합니다.")

    resolved_read_mode = _resolve_read_mode(mode, read_mode)
    print(f"[gemini-repair] Current Mode: {mode}")
    print(
        f"[gemini-repair] limit={limit}, batch_size={batch_size}, "
        f"stop_on_error={stop_on_error}, read_mode={resolved_read_mode}, target_mode={target_mode}"
    )

    fetcher = _fetch_missing_bills if target_mode == "missing" else _fetch_latest_bills
    targets = fetcher(mode=mode, limit=limit, read_mode=read_mode)

    if target_mode == "latest" and targets:
        for target in targets:
            target["brief_summary"] = None
            target["gpt_summary"] = None

    summarizer = GeminiCliSummarizer()
    items: List[Dict[str, Any]] = []
    success_items: List[Dict[str, Any]] = []

    for start in range(0, len(targets), batch_size):
        batch = targets[start:start + batch_size]
        if not batch:
            continue

        batch_df = pd.DataFrame(batch)
        summarizer.failed_bills = []
        result_df = summarizer.AI_structured_summarize(batch_df)
        failure_map = {
            str(entry.get("bill_id")): str(entry.get("error"))
            for entry in summarizer.failed_bills
            if entry.get("bill_id") is not None
        }

        for row in result_df.to_dict("records"):
            item = _normalize_item(row, failure_map)
            items.append(item)
            if item["status"] == "success":
                success_items.append(item)

        if stop_on_error and failure_map:
            print("[gemini-repair] stop_on_error=True, batch failure detected.")
            break

    report = {
        "execution_mode": mode,
        "requested_limit": limit,
        "batch_size": batch_size,
        "stop_on_error": stop_on_error,
        "read_mode": resolved_read_mode,
        "target_mode": target_mode,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "stats": {
            "target_count": len(targets),
            "processed_count": len(items),
            "success_count": sum(1 for item in items if item["status"] == "success"),
            "failure_count": sum(1 for item in items if item["status"] == "failed"),
            "db_upserted_count": 0,
        },
        "items": items,
        "output_path": output_path,
    }

    _write_json_output(report, output_path)

    if report["stats"]["target_count"] > 0 and report["stats"]["success_count"] == 0:
        raise RuntimeError(f"Gemini 요약이 모두 실패했습니다. 산출물: {output_path}")

    if stop_on_error and report["stats"]["failure_count"] > 0:
        raise RuntimeError(f"Gemini 요약 실패가 발생해 실행을 중단했습니다. 산출물: {output_path}")

    if mode != "dry_run":
        report["stats"]["db_upserted_count"] = _upsert_successful_items(success_items, mode)

    print(
        "[gemini-repair] completed "
        f"targets={report['stats']['target_count']} "
        f"success={report['stats']['success_count']} "
        f"failure={report['stats']['failure_count']} "
        f"upserted={report['stats']['db_upserted_count']}"
    )
    return report
