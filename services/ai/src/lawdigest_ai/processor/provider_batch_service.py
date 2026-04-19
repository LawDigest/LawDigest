from __future__ import annotations

import json
import os
import time
from typing import Any, Callable, Dict, List, Literal

import pymysql

from lawdigest_ai.config import GEMINI_BATCH_MODEL
from lawdigest_ai.processor.batch_utils import (
    create_batch_job_with_items,
    ensure_status_tables,
    fetch_jobs_for_polling,
    fetch_unsummarized_bills,
    update_job_status,
    write_jsonl_tempfile,
)
from lawdigest_ai.processor.providers import BatchProviderBase, get_batch_provider

SubmitProvider = Literal["openai", "gemini"]
IngestProvider = Literal["openai", "gemini", "all"]
INGEST_PROVIDERS: tuple[SubmitProvider, ...] = ("openai", "gemini")

DEFAULT_BATCH_MODELS: dict[SubmitProvider, str] = {
    "openai": "gpt-4o-mini",
    "gemini": GEMINI_BATCH_MODEL,
}


def _detect_endpoint(request_rows: List[Dict[str, Any]]) -> str:
    if not request_rows:
        return "/v1/chat/completions"

    first_row = request_rows[0]
    endpoint = first_row.get("url")
    if isinstance(endpoint, str) and endpoint:
        return endpoint

    return "/v1/chat/completions"


def _fetch_job_bill_ids(conn: pymysql.connections.Connection, job_id: int) -> List[str]:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT bill_id FROM ai_batch_items WHERE job_id=%s ORDER BY id ASC",
            (job_id,),
        )
        rows = cursor.fetchall()
    return [row["bill_id"] for row in rows]


def _fetch_jobs_for_all_providers(
    conn: pymysql.connections.Connection,
    max_jobs: int,
    fetch_jobs: Callable[..., List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    if max_jobs <= 0:
        return []

    provider_job_groups = [
        list(fetch_jobs(conn, max_jobs=max_jobs, provider=provider_name))
        for provider_name in INGEST_PROVIDERS
    ]
    start_index = int(time.time()) % len(INGEST_PROVIDERS)
    rotated_groups = provider_job_groups[start_index:] + provider_job_groups[:start_index]

    jobs: List[Dict[str, Any]] = []
    while len(jobs) < max_jobs:
        progressed = False
        for group in rotated_groups:
            if not group:
                continue
            jobs.append(group.pop(0))
            progressed = True
            if len(jobs) >= max_jobs:
                break
        if not progressed:
            break

    return jobs


def _resolve_submit_model(provider: SubmitProvider, model: str | None) -> str:
    if model:
        return model
    return DEFAULT_BATCH_MODELS[provider]


def apply_batch_results_for_provider(
    conn: pymysql.connections.Connection,
    job_id: int,
    output_jsonl: str,
    provider: BatchProviderBase,
) -> tuple[int, int]:
    expected_bill_ids = _fetch_job_bill_ids(conn, job_id)
    parsed_results = provider.parse_output_lines(output_jsonl, expected_bill_ids=expected_bill_ids)

    success = failed = 0
    with conn.cursor() as cursor:
        for result in parsed_results:
            if not result.bill_id:
                failed += 1
                continue

            if result.error:
                affected_rows = cursor.execute(
                    "UPDATE ai_batch_items SET status='FAILED', retry_count=retry_count+1, "
                    "error_message=%s, processed_at=NOW() "
                    "WHERE job_id=%s AND bill_id=%s AND status='SUBMITTED'",
                    (result.error, job_id, result.bill_id),
                )
                if affected_rows:
                    failed += 1
                continue

            bill_updated = cursor.execute(
                "UPDATE Bill SET brief_summary=%s, gpt_summary=%s, summary_tags=%s, modified_date=NOW() "
                "WHERE bill_id=%s",
                (
                    result.brief_summary,
                    result.gpt_summary,
                    json.dumps(result.tags or [], ensure_ascii=False),
                    result.bill_id,
                ),
            )
            if not bill_updated:
                failed_update = cursor.execute(
                    "UPDATE ai_batch_items SET status='FAILED', retry_count=retry_count+1, "
                    "error_message=%s, processed_at=NOW() "
                    "WHERE job_id=%s AND bill_id=%s AND status='SUBMITTED'",
                    ("Bill row를 찾지 못했습니다.", job_id, result.bill_id),
                )
                if failed_update:
                    failed += 1
                continue

            affected_rows = cursor.execute(
                "UPDATE ai_batch_items SET status='DONE', error_message=NULL, processed_at=NOW() "
                "WHERE job_id=%s AND bill_id=%s AND status='SUBMITTED'",
                (job_id, result.bill_id),
            )
            if not affected_rows:
                continue

            success += 1

        remaining_failed = cursor.execute(
            "UPDATE ai_batch_items SET status='FAILED', retry_count=retry_count+1, "
            "error_message=COALESCE(error_message, 'output에 결과가 없습니다.'), processed_at=NOW() "
            "WHERE job_id=%s AND status='SUBMITTED'",
            (job_id,),
        )
        failed += remaining_failed if isinstance(remaining_failed, int) else 0

        cursor.execute(
            "UPDATE ai_batch_jobs "
            "SET success_count=success_count+%s, failed_count=failed_count+%s WHERE id=%s",
            (success, failed, job_id),
        )

    conn.commit()
    return success, failed


def submit_batches(
    conn: pymysql.connections.Connection,
    limit: int = 200,
    model: str | None = None,
    mode: str = "dry_run",
    provider: SubmitProvider = "openai",
    ensure_tables: Callable[[pymysql.connections.Connection], None] = ensure_status_tables,
    fetch_bills: Callable[[pymysql.connections.Connection, int], List[Dict[str, Any]]] = fetch_unsummarized_bills,
    provider_factory: Callable[[SubmitProvider], BatchProviderBase] = get_batch_provider,
    jsonl_writer: Callable[[List[Dict[str, Any]]], str] = write_jsonl_tempfile,
    create_job: Callable[..., int] = create_batch_job_with_items,
) -> Dict[str, Any]:
    resolved_model = _resolve_submit_model(provider, model)
    ensure_tables(conn)
    bills = fetch_bills(conn, limit=limit)
    if not bills:
        print(f"[batch-submit] provider={provider} 제출 대상 법안이 없습니다.")
        return {"submitted": 0, "mode": mode, "provider": provider}

    if mode == "dry_run":
        print(f"[batch-submit] [DRY_RUN] provider={provider} {len(bills)}개 법안 제출 대상 선정. (실제 제출 안 함)")
        return {"submitted": len(bills), "mode": "dry_run", "provider": provider}

    provider_instance = provider_factory(provider)
    request_rows = provider_instance.build_request_rows(bills, model=resolved_model)
    jsonl_path = jsonl_writer(request_rows)
    try:
        input_file_id = provider_instance.upload_batch_file(jsonl_path, display_name=None)
        batch_state = provider_instance.create_batch_job(
            model=resolved_model,
            source_file_name=input_file_id,
            display_name=None,
        )
        provider_name = provider_instance.provider_name.value
        batch_id = batch_state.batch_id
        job_id = create_job(
            conn=conn,
            batch_id=batch_id,
            input_file_id=input_file_id,
            model=resolved_model,
            bill_ids=[bill["bill_id"] for bill in bills],
            status=(batch_state.status or "SUBMITTED").upper(),
            provider=provider_name,
            endpoint=_detect_endpoint(request_rows),
        )
        print(
            f"[batch-submit] [{mode}] provider={provider_name} job_id={job_id} "
            f"batch_id={batch_id} count={len(bills)}"
        )
        return {
            "submitted": len(bills),
            "batch_id": batch_id,
            "job_id": job_id,
            "mode": mode,
            "provider": provider_name,
        }
    finally:
        if os.path.exists(jsonl_path):
            os.remove(jsonl_path)


def ingest_batch_results_for_provider(
    conn: pymysql.connections.Connection,
    max_jobs: int = 10,
    mode: str = "dry_run",
    provider: IngestProvider = "all",
    fetch_jobs: Callable[..., List[Dict[str, Any]]] = fetch_jobs_for_polling,
    provider_factory: Callable[[SubmitProvider], BatchProviderBase] = get_batch_provider,
    apply_results: Callable[..., tuple[int, int]] = apply_batch_results_for_provider,
    update_status: Callable[..., None] = update_job_status,
) -> Dict[str, Any]:
    provider_filter = None if provider == "all" else provider
    if provider == "all":
        jobs = _fetch_jobs_for_all_providers(conn, max_jobs=max_jobs, fetch_jobs=fetch_jobs)
    else:
        jobs = fetch_jobs(conn, max_jobs=max_jobs, provider=provider_filter)
    if not jobs:
        print(f"[batch-ingest] provider={provider} 폴링 대상 작업이 없습니다.")
        return {"processed_jobs": 0, "mode": mode, "provider": provider}

    total_success = total_failed = 0
    providers_by_name: dict[str, BatchProviderBase] = {}

    for job in jobs:
        job_id = int(job["id"])
        batch_id = job["batch_id"]
        job_provider = str(job.get("provider") or "openai")
        try:
            provider_instance = providers_by_name.setdefault(
                job_provider,
                provider_factory(job_provider),  # type: ignore[arg-type]
            )
            batch_state = provider_instance.get_batch_job(batch_id)
            status = (batch_state.status or "").upper()

            if status != "COMPLETED" or not batch_state.output_file_id:
                update_status(
                    conn=conn,
                    job_id=job_id,
                    status=status,
                    output_file_id=batch_state.output_file_id,
                    error_file_id=batch_state.error_file_id,
                    error_message=batch_state.error_message,
                )
                print(
                    f"[batch-ingest] provider={job_provider} batch_id={batch_id} "
                    f"status={status} - 아직 완료되지 않음"
                )
                continue

            if mode == "dry_run":
                update_status(
                    conn=conn,
                    job_id=job_id,
                    status=status,
                    output_file_id=batch_state.output_file_id,
                    error_file_id=batch_state.error_file_id,
                    error_message=batch_state.error_message,
                )
                print(
                    f"[batch-ingest] [DRY_RUN] provider={job_provider} "
                    f"batch_id={batch_id} COMPLETED - 결과 적재 생략"
                )
                continue

            try:
                output_jsonl = provider_instance.download_output_file(batch_state.output_file_id)
                success, failed = apply_results(conn, job_id, output_jsonl, provider_instance)
            except Exception as exc:
                conn.rollback()
                update_status(
                    conn=conn,
                    job_id=job_id,
                    status="FINALIZING",
                    output_file_id=batch_state.output_file_id,
                    error_file_id=batch_state.error_file_id,
                    error_message=str(exc),
                )
                print(
                    f"[batch-ingest] provider={job_provider} batch_id={batch_id} "
                    f"결과 적용 실패: {exc}"
                )
                continue

            update_status(
                conn=conn,
                job_id=job_id,
                status=status,
                output_file_id=batch_state.output_file_id,
                error_file_id=batch_state.error_file_id,
                error_message=batch_state.error_message,
            )
            total_success += success
            total_failed += failed
            print(
                f"[batch-ingest] provider={job_provider} batch_id={batch_id} "
                f"적재 완료: 성공={success}, 실패={failed}"
            )
        except Exception as exc:
            print(
                f"[batch-ingest] provider={job_provider} batch_id={batch_id} "
                f"처리 실패: {exc}"
            )
            continue

    return {
        "processed_jobs": len(jobs),
        "total_success": total_success,
        "total_failed": total_failed,
        "mode": mode,
        "provider": provider,
    }
