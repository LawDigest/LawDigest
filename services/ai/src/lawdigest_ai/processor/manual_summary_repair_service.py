from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal

from lawdigest_ai.db import get_db_connection, update_bill_summary
from lawdigest_ai.observability import trace_span
from lawdigest_ai.processor.provider_instant_service import (
    resolve_instant_model,
    summarize_bills_with_provider,
)

RepairProvider = Literal["openai", "gemini"]
DEFAULT_OUTPUT_PATH = "/tmp/lawdigest_missing_summaries.json"


def _write_json_output(payload: Dict[str, Any], output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _db_mode_for_execution(mode: str) -> str:
    return "prod" if mode == "prod" else "test"


def _fetch_missing_bills(mode: str, limit: int) -> List[Dict[str, Any]]:
    query = """
    SELECT
        bill_id,
        bill_name,
        summary,
        proposers,
        proposer_kind,
        title,
        gpt_summary,
        propose_date,
        stage
    FROM Bill
    WHERE
        (gpt_summary IS NULL OR gpt_summary = '' OR title IS NULL OR title = '')
        AND summary IS NOT NULL
        AND summary != ''
    ORDER BY propose_date DESC
    """

    conn = get_db_connection(mode=_db_mode_for_execution(mode))
    try:
        with conn.cursor() as cur:
            cur.execute(query + " LIMIT %s", (limit,))
            return list(cur.fetchall())
    finally:
        conn.close()


def _to_report_item(source: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    error = result.get("error")
    if not error and (not result.get("title") or not result.get("gpt_summary")):
        error = "요약 결과에 필수 필드가 비어 있습니다."

    return {
        "bill_id": source.get("bill_id"),
        "bill_name": source.get("bill_name"),
        "title": result.get("title"),
        "gpt_summary": result.get("gpt_summary"),
        "summary_tags": result.get("summary_tags"),
        "category": result.get("category"),
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
            title=item.get("title"),
            gpt_summary=item.get("gpt_summary"),
            summary_tags=item.get("summary_tags"),
            mode=_db_mode_for_execution(mode),
            category=item.get("category"),
        )
        upserted += 1
    return upserted


def run_manual_summary_repair(
    *,
    mode: str = "dry_run",
    output_path: str = DEFAULT_OUTPUT_PATH,
    batch_size: int = 10,
    limit: int = 200,
    provider: RepairProvider = "openai",
    model: str | None = None,
) -> Dict[str, Any]:
    if batch_size < 1:
        raise ValueError("batch_size는 1 이상이어야 합니다.")
    if limit < 1:
        raise ValueError("limit는 1 이상이어야 합니다.")

    resolved_model = resolve_instant_model(provider, model)
    print(
        f"[manual-summary-repair] mode={mode}, provider={provider}, "
        f"model={resolved_model}, limit={limit}, batch_size={batch_size}"
    )

    with trace_span(
        "manual_summary_repair",
        input={"mode": mode, "provider": provider, "model": resolved_model, "limit": limit, "batch_size": batch_size},
    ):
        targets = _fetch_missing_bills(mode, limit=limit)
    items: List[Dict[str, Any]] = []

    if not targets:
        report = {
            "execution_mode": mode,
            "provider": provider,
            "model": resolved_model,
            "limit": limit,
            "batch_size": batch_size,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "stats": {
                "target_count": 0,
                "processed_count": 0,
                "success_count": 0,
                "failure_count": 0,
                "db_upserted_count": 0,
            },
            "items": [],
            "output_path": output_path,
        }
        _write_json_output(report, output_path)
        return report

    for start in range(0, len(targets), batch_size):
        batch = targets[start:start + batch_size]
        if not batch:
            continue

        results = summarize_bills_with_provider(
            batch,
            provider=provider,
            model=model,
        )
        for source, result in zip(batch, results):
            items.append(_to_report_item(source, result))

    report = {
        "execution_mode": mode,
        "provider": provider,
        "model": resolved_model,
        "limit": limit,
        "batch_size": batch_size,
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

    if mode != "dry_run":
        report["stats"]["db_upserted_count"] = _upsert_successful_items(items, mode)

    return report
