from __future__ import annotations

import hashlib
from datetime import timedelta
from typing import Any

from lawdigest_ai.db import get_db_connection
from lawdigest_ai.processor.agentic_bill_report import _strip_term_tooltips


def report_hash(report_body: str) -> str:
    return hashlib.sha256(report_body.encode("utf-8")).hexdigest()


def _bill_id_filter(bill_ids: list[str] | None) -> tuple[str, list[Any]]:
    if bill_ids is None:
        return "", []
    if not bill_ids:
        return " AND 1 = 0", []
    placeholders = ", ".join(["%s"] * len(bill_ids))
    return f" AND bill.bill_id IN ({placeholders})", list(bill_ids)


def _reconcile_with_cursor(cursor: Any, bill_ids: list[str] | None = None) -> int:
    bill_filter, params = _bill_id_filter(bill_ids)
    cursor.execute(
        f"""
        INSERT INTO BillReportTooltip (
            bill_id, source_report_hash, rendered_summary, status,
            applied_count, attempt_count, claimed_at, processed_at
        )
        SELECT
            bill.bill_id, SHA2(bill.gpt_summary, 256), NULL, 'PENDING',
            0, 0, NULL, NULL
        FROM Bill bill
        WHERE bill.gpt_summary IS NOT NULL
          AND LENGTH(TRIM(bill.gpt_summary)) > 0
          AND bill.gpt_summary LIKE %s
          {bill_filter}
        ON DUPLICATE KEY UPDATE
            rendered_summary = IF(
                BillReportTooltip.source_report_hash <> VALUES(source_report_hash),
                NULL,
                BillReportTooltip.rendered_summary
            ),
            status = IF(
                BillReportTooltip.source_report_hash <> VALUES(source_report_hash),
                'PENDING',
                BillReportTooltip.status
            ),
            applied_count = IF(
                BillReportTooltip.source_report_hash <> VALUES(source_report_hash),
                0,
                BillReportTooltip.applied_count
            ),
            attempt_count = IF(
                BillReportTooltip.source_report_hash <> VALUES(source_report_hash),
                0,
                BillReportTooltip.attempt_count
            ),
            model_name = IF(
                BillReportTooltip.source_report_hash <> VALUES(source_report_hash),
                NULL,
                BillReportTooltip.model_name
            ),
            last_error = IF(
                BillReportTooltip.source_report_hash <> VALUES(source_report_hash),
                NULL,
                BillReportTooltip.last_error
            ),
            claimed_at = IF(
                BillReportTooltip.source_report_hash <> VALUES(source_report_hash),
                NULL,
                BillReportTooltip.claimed_at
            ),
            processed_at = IF(
                BillReportTooltip.source_report_hash <> VALUES(source_report_hash),
                NULL,
                BillReportTooltip.processed_at
            ),
            source_report_hash = VALUES(source_report_hash)
        """,
        ["%## 쉬운 요약%", *params],
    )
    return int(cursor.rowcount)


def reconcile_bill_tooltip_states(*, mode: str, bill_ids: list[str] | None = None) -> int:
    conn = get_db_connection(mode=mode)
    try:
        conn.begin()
        with conn.cursor() as cursor:
            changed = _reconcile_with_cursor(cursor, bill_ids)
        conn.commit()
        return changed
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _target_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **dict(row),
            "report_body": f"# {row['bill_name']}\n\n{str(row['gpt_summary']).strip()}\n",
        }
        for row in rows
    ]


def preview_bill_tooltip_targets(
    *,
    mode: str,
    limit: int,
    target: str = "missing",
    bill_ids: list[str] | None = None,
    lease_timeout: timedelta = timedelta(minutes=30),
) -> list[dict[str, Any]]:
    bill_filter, bill_params = _bill_id_filter(bill_ids)
    state_filter = "1 = 1" if target == "all" else """
        (
            tooltip.bill_id IS NULL
            OR tooltip.source_report_hash <> SHA2(bill.gpt_summary, 256)
            OR tooltip.status IN ('PENDING', 'FAILED')
            OR (
                tooltip.status = 'RUNNING'
                AND tooltip.claimed_at < DATE_SUB(NOW(6), INTERVAL %s SECOND)
            )
        )
    """
    params: list[Any] = [] if target == "all" else [int(lease_timeout.total_seconds())]
    params.extend(bill_params)
    params.append(limit)
    conn = get_db_connection(mode=mode)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    bill.bill_id,
                    bill.bill_name,
                    bill.brief_summary,
                    bill.summary_tags,
                    bill.gpt_summary,
                    SHA2(bill.gpt_summary, 256) AS source_report_hash
                FROM Bill bill
                LEFT JOIN BillReportTooltip tooltip ON tooltip.bill_id = bill.bill_id
                WHERE bill.gpt_summary IS NOT NULL
                  AND LENGTH(TRIM(bill.gpt_summary)) > 0
                  AND bill.gpt_summary LIKE %s
                  AND {state_filter}
                  {bill_filter}
                ORDER BY bill.propose_date DESC, bill.bill_id DESC
                LIMIT %s
                """,
                ["%## 쉬운 요약%", *params],
            )
            return _target_rows(list(cursor.fetchall()))
    finally:
        conn.close()


def claim_bill_tooltip_targets(
    *,
    mode: str,
    limit: int,
    target: str = "missing",
    bill_ids: list[str] | None = None,
    lease_timeout: timedelta = timedelta(minutes=30),
) -> list[dict[str, Any]]:
    bill_filter, bill_params = _bill_id_filter(bill_ids)
    state_filter = """
        (
            tooltip.status IN ('PENDING', 'FAILED')
            OR (
                tooltip.status = 'RUNNING'
                AND tooltip.claimed_at < DATE_SUB(NOW(6), INTERVAL %s SECOND)
            )
        )
    """
    if target == "all":
        state_filter = """
            (
                tooltip.status <> 'RUNNING'
                OR tooltip.claimed_at < DATE_SUB(NOW(6), INTERVAL %s SECOND)
            )
        """
    params: list[Any] = [int(lease_timeout.total_seconds()), *bill_params, limit]
    conn = get_db_connection(mode=mode)
    try:
        conn.begin()
        with conn.cursor() as cursor:
            _reconcile_with_cursor(cursor, bill_ids)
            cursor.execute(
                f"""
                SELECT
                    bill.bill_id,
                    bill.bill_name,
                    bill.brief_summary,
                    bill.summary_tags,
                    bill.gpt_summary,
                    tooltip.source_report_hash
                FROM BillReportTooltip tooltip
                JOIN Bill bill ON bill.bill_id = tooltip.bill_id
                WHERE tooltip.source_report_hash = SHA2(bill.gpt_summary, 256)
                  AND {state_filter}
                  {bill_filter}
                ORDER BY bill.propose_date DESC, bill.bill_id DESC
                LIMIT %s
                FOR UPDATE SKIP LOCKED
                """,
                params,
            )
            rows = list(cursor.fetchall())
            if rows:
                claimed_ids = [str(row["bill_id"]) for row in rows]
                placeholders = ", ".join(["%s"] * len(claimed_ids))
                cursor.execute(
                    f"""
                    UPDATE BillReportTooltip
                    SET status = 'RUNNING',
                        attempt_count = attempt_count + 1,
                        claimed_at = NOW(6),
                        processed_at = NULL,
                        last_error = NULL
                    WHERE bill_id IN ({placeholders})
                    """,
                    claimed_ids,
                )
        conn.commit()
        return _target_rows(rows)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def complete_bill_tooltip_target(
    *,
    mode: str,
    bill_id: str,
    source_report_hash: str,
    status: str,
    rendered_summary: str | None,
    applied_count: int,
    model_name: str,
) -> bool:
    if status not in {"APPLIED", "SKIPPED"}:
        raise ValueError("status must be APPLIED or SKIPPED")
    if status == "APPLIED" and not rendered_summary:
        raise ValueError("APPLIED status requires rendered_summary")

    conn = get_db_connection(mode=mode)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE BillReportTooltip AS tooltip
                JOIN Bill AS bill ON bill.bill_id = tooltip.bill_id
                SET tooltip.status = %s,
                    tooltip.rendered_summary = %s,
                    tooltip.applied_count = %s,
                    tooltip.model_name = %s,
                    tooltip.last_error = NULL,
                    tooltip.claimed_at = NULL,
                    tooltip.processed_at = NOW(6)
                WHERE tooltip.bill_id = %s
                  AND tooltip.status = 'RUNNING'
                  AND tooltip.source_report_hash = %s
                  AND tooltip.source_report_hash = SHA2(bill.gpt_summary, 256)
                """,
                (status, rendered_summary, applied_count, model_name, bill_id, source_report_hash),
            )
            completed = cursor.rowcount == 1
        conn.commit()
        return completed
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fail_bill_tooltip_target(
    *,
    mode: str,
    bill_id: str,
    source_report_hash: str,
    error: str,
    model_name: str,
) -> bool:
    conn = get_db_connection(mode=mode)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE BillReportTooltip AS tooltip
                JOIN Bill AS bill ON bill.bill_id = tooltip.bill_id
                SET tooltip.status = 'FAILED',
                    tooltip.rendered_summary = NULL,
                    tooltip.applied_count = 0,
                    tooltip.model_name = %s,
                    tooltip.last_error = %s,
                    tooltip.claimed_at = NULL,
                    tooltip.processed_at = NOW(6)
                WHERE tooltip.bill_id = %s
                  AND tooltip.status = 'RUNNING'
                  AND tooltip.source_report_hash = %s
                  AND tooltip.source_report_hash = SHA2(bill.gpt_summary, 256)
                """,
                (model_name, error[:65535], bill_id, source_report_hash),
            )
            completed = cursor.rowcount == 1
        conn.commit()
        return completed
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def migrate_inline_tooltips(*, mode: str, batch_size: int = 100) -> dict[str, Any]:
    if mode not in {"test", "prod"}:
        raise ValueError("inline tooltip migration requires test or prod mode")
    if batch_size < 1:
        raise ValueError("batch_size must be positive")

    conn = get_db_connection(mode=mode)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT bill_id, gpt_summary
                FROM Bill
                WHERE gpt_summary LIKE %s
                ORDER BY bill_id
                """,
                ("%{{%:%}}%",),
            )
            rows = list(cursor.fetchall())
    finally:
        conn.close()

    prepared: list[tuple[str, str, str, str]] = []
    for row in rows:
        bill_id = str(row["bill_id"])
        original = str(row["gpt_summary"] or "")
        clean = _strip_term_tooltips(original)
        if clean == original:
            raise RuntimeError(f"inline tooltip parser did not change {bill_id}")
        if "{{" in clean or "}}" in clean:
            raise RuntimeError(f"unmatched tooltip braces remain in {bill_id}")
        prepared.append((bill_id, original, clean, report_hash(clean)))

    migrated_ids: list[str] = []
    for start in range(0, len(prepared), batch_size):
        batch = prepared[start : start + batch_size]
        conn = get_db_connection(mode=mode)
        try:
            conn.begin()
            with conn.cursor() as cursor:
                for bill_id, original, clean, source_hash in batch:
                    cursor.execute(
                        """
                        UPDATE Bill
                        SET gpt_summary = %s,
                            modified_date = NOW(6)
                        WHERE bill_id = %s
                          AND gpt_summary = %s
                        """,
                        (clean, bill_id, original),
                    )
                    if cursor.rowcount != 1:
                        raise RuntimeError(f"bill report changed during inline tooltip migration: {bill_id}")
                    cursor.execute(
                        """
                        INSERT INTO BillReportTooltip (
                            bill_id, source_report_hash, rendered_summary, status,
                            applied_count, attempt_count, model_name, last_error,
                            claimed_at, processed_at
                        ) VALUES (%s, %s, NULL, 'PENDING', 0, 0, NULL, NULL, NULL, NULL) AS new
                        ON DUPLICATE KEY UPDATE
                            source_report_hash = new.source_report_hash,
                            rendered_summary = NULL,
                            status = 'PENDING',
                            applied_count = 0,
                            attempt_count = 0,
                            model_name = NULL,
                            last_error = NULL,
                            claimed_at = NULL,
                            processed_at = NULL
                        """,
                        (bill_id, source_hash),
                    )
            conn.commit()
            migrated_ids.extend(item[0] for item in batch)
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    return {
        "mode": mode,
        "matched_count": len(rows),
        "migrated_count": len(migrated_ids),
        "bill_ids": migrated_ids,
    }
