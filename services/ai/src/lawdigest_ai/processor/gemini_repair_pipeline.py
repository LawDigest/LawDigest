from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from lawdigest_ai.db import get_db_connection, update_bill_summary
from lawdigest_ai.processor.gemini_cli_summarizer import build_cli_summarizer
from lawdigest_ai.observability import trace_generation, trace_span


DEFAULT_OUTPUT_PATH = "/tmp/lawdigest_ai_summary_results.json"


def _print_progress(message: str) -> None:
    print(f"[cli-summary-repair] {message}", flush=True)


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
        title,
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


def _normalize_item(
    row: Dict[str, Any],
    failure_map: Dict[str, str],
    usage_map: Dict[str, dict[str, int]],
) -> Dict[str, Any]:
    ai_title = row.get("title")
    ai_summary = row.get("gpt_summary")
    bill_id = row.get("bill_id")
    error = failure_map.get(str(bill_id))

    if not error and (not ai_title or not ai_summary):
        error = "Gemini 요약 결과에 필수 필드가 비어 있습니다."

    item = {
        "bill_id": bill_id,
        "bill_name": row.get("bill_name"),
        "ai_title": ai_title,
        "ai_summary": ai_summary,
        "summary_tags": row.get("summary_tags"),
        "category": row.get("category"),
        "status": "failed" if error else "success",
        "error": error,
    }
    usage = usage_map.get(str(bill_id)) if isinstance(usage_map, dict) else None
    if isinstance(usage, dict):
        item["usage"] = usage
    return item


def _sum_usage(items: List[Dict[str, Any]]) -> Dict[str, int]:
    totals: Dict[str, int] = {}
    for item in items:
        usage = item.get("usage")
        if not isinstance(usage, dict):
            continue
        for key, value in usage.items():
            if isinstance(value, int):
                totals[key] = totals.get(key, 0) + value
    return totals


def _upsert_successful_item(item: Dict[str, Any], mode: str) -> bool:
    if item["status"] != "success":
        return False
    update_bill_summary(
        bill_id=str(item["bill_id"]),
        title=item.get("ai_title"),
        gpt_summary=item.get("ai_summary"),
        summary_tags=item.get("summary_tags"),
        mode=_db_mode_for_execution(mode),
        category=item.get("category"),
    )
    return True


def run_gemini_repair_pipeline(
    mode: str = "dry_run",
    limit: int = 20,
    batch_size: int = 5,
    output_path: str = DEFAULT_OUTPUT_PATH,
    stop_on_error: bool = False,
    read_mode: str | None = None,
    target_mode: str = "missing",
    cli_provider: str = "gemini",
) -> Dict[str, Any]:
    if limit < 1:
        raise ValueError("limit는 1 이상이어야 합니다.")
    if batch_size < 1:
        raise ValueError("batch_size는 1 이상이어야 합니다.")
    if target_mode not in {"missing", "latest"}:
        raise ValueError("target_mode는 missing 또는 latest 여야 합니다.")

    started_at = time.monotonic()
    resolved_read_mode = _resolve_read_mode(mode, read_mode)
    _print_progress(f"start mode={mode}")
    _print_progress(
        f"config limit={limit}, batch_size={batch_size}, "
        f"stop_on_error={stop_on_error}, read_mode={resolved_read_mode}, target_mode={target_mode}"
    )

    fetcher = _fetch_missing_bills if target_mode == "missing" else _fetch_latest_bills
    with trace_span(
        "gemini_repair_pipeline",
        input={
            "mode": mode,
            "limit": limit,
            "batch_size": batch_size,
            "stop_on_error": stop_on_error,
            "read_mode": read_mode,
            "target_mode": target_mode,
            "cli_provider": cli_provider,
        },
    ) as root_span:
        targets = fetcher(mode=mode, limit=limit, read_mode=read_mode)
        total_batches = (len(targets) + batch_size - 1) // batch_size if targets else 0
        _print_progress(f"loaded targets={len(targets)}, batches={total_batches}")

        if target_mode == "latest" and targets:
            for target in targets:
                target["title"] = None
                target["gpt_summary"] = None

        summarizer = build_cli_summarizer(cli_provider)
        items = []
        db_upserted_count = 0

        for start in range(0, len(targets), batch_size):
            batch = targets[start:start + batch_size]
            if not batch:
                continue
            batch_number = (start // batch_size) + 1
            batch_started_at = time.monotonic()
            batch_ids = [str(row.get("bill_id")) for row in batch if row.get("bill_id") is not None]
            _print_progress(
                f"batch {batch_number}/{total_batches} start "
                f"items={len(batch)}, processed={len(items)}/{len(targets)}, bill_ids={','.join(batch_ids)}"
            )

            with trace_generation(
                root_span,
                name=f"{cli_provider}_cli_batch_summarize",
                model=f"{cli_provider}-cli",
                input={"batch_size": len(batch), "start": start},
            ) as generation:
                batch_df = pd.DataFrame(batch)
                summarizer.failed_bills = []
                result_df = summarizer.AI_structured_summarize(batch_df)
                failure_map = {
                    str(entry.get("bill_id")): str(entry.get("error"))
                    for entry in summarizer.failed_bills
                    if entry.get("bill_id") is not None
                }

                for row in result_df.to_dict("records"):
                    item = _normalize_item(row, failure_map, summarizer.usage_by_bill_id)
                    items.append(item)
                    if item["status"] == "success":
                        if mode != "dry_run" and _upsert_successful_item(item, mode):
                            db_upserted_count += 1
                            _print_progress(
                                f"db upsert item done bill_id={item['bill_id']} "
                                f"upserted={db_upserted_count}"
                            )

                usage_totals = _sum_usage(items)
                _print_progress(
                    f"batch {batch_number}/{total_batches} done "
                    f"elapsed={time.monotonic() - batch_started_at:.1f}s, "
                    f"processed={len(items)}/{len(targets)}, "
                    f"success={sum(1 for item in items if item['status'] == 'success')}, "
                    f"failure={sum(1 for item in items if item['status'] == 'failed')}, "
                    f"input_tokens={usage_totals.get('input_tokens', 0)}, "
                    f"output_tokens={usage_totals.get('output_tokens', 0)}"
                )

                if stop_on_error and failure_map:
                    _print_progress("stop_on_error=True, batch failure detected")
                    if generation is not None:
                        generation.update(status_message="batch failed and stop_on_error enabled")
                    break

    report = {
        "execution_mode": mode,
        "requested_limit": limit,
        "batch_size": batch_size,
        "stop_on_error": stop_on_error,
        "read_mode": resolved_read_mode,
        "target_mode": target_mode,
        "cli_provider": cli_provider,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "stats": {
            "target_count": len(targets),
            "processed_count": len(items),
            "success_count": sum(1 for item in items if item["status"] == "success"),
            "failure_count": sum(1 for item in items if item["status"] == "failed"),
            "db_upserted_count": db_upserted_count,
            "token_usage_available_count": sum(1 for item in items if isinstance(item.get("usage"), dict)),
            "usage_totals": _sum_usage(items),
        },
        "items": items,
        "output_path": output_path,
    }

    if report["stats"]["target_count"] > 0 and report["stats"]["success_count"] == 0:
        _write_json_output(report, output_path)
        raise RuntimeError(f"CLI 요약이 모두 실패했습니다. 산출물: {output_path}")

    if stop_on_error and report["stats"]["failure_count"] > 0:
        _write_json_output(report, output_path)
        raise RuntimeError(f"CLI 요약 실패가 발생해 실행을 중단했습니다. 산출물: {output_path}")

    if mode == "dry_run":
        _print_progress("db upsert skipped dry_run")

    _write_json_output(report, output_path)
    _print_progress(f"wrote output={output_path}")

    _print_progress(
        "completed "
        f"targets={report['stats']['target_count']} "
        f"success={report['stats']['success_count']} "
        f"failure={report['stats']['failure_count']} "
        f"upserted={report['stats']['db_upserted_count']} "
        f"elapsed={time.monotonic() - started_at:.1f}s"
    )
    return report
