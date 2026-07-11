from __future__ import annotations

import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lawdigest_ai.db import get_db_connection, update_bill_summary
from lawdigest_ai.processor.agentic_bill_report import (
    DEFAULT_BATCH_SESSION_SIZE,
    DEFAULT_CODEX_MODEL,
    MAX_BATCH_SESSION_SIZE,
    CodexBillReportAgent,
    _apply_legal_term_tooltip_decisions,
    _build_db_summary_payload,
    _db_mode_for_execution,
    _parse_codex_json_metadata,
    _parse_legal_term_tooltip_decisions,
    _repair_term_tooltip_particles,
    _resolve_read_mode,
    _slugify_bill_id,
    _strip_term_tooltips,
    _validate_report_body,
)
from lawdigest_ai.processor.legal_term_glossary import LegalTermEntry, build_legal_term_tooltip_entries


DEFAULT_TOOLTIP_OUTPUT_DIR = "/tmp/lawdigest-bill-agent-tooltips"
TOOLTIP_TARGETS = ("missing", "all")


def _candidate_to_dict(entry: LegalTermEntry) -> dict[str, Any]:
    return {
        "term": entry.term,
        "aliases": list(entry.aliases),
        "definition": entry.definition,
        "source": entry.source,
    }


def build_bill_tooltip_prompt(
    *,
    bill: dict[str, Any],
    report_body: str,
    candidates: list[LegalTermEntry],
) -> str:
    candidate_payload = [_candidate_to_dict(entry) for entry in candidates]
    return (
        "작업: 이미 완성된 Lawdigest 법안 리포트에 필요한 법률용어 툴팁 후보만 판정하세요.\n"
        "리포트 본문을 다시 작성하거나 수정하지 마세요. 새로운 사실이나 정의를 만들지 마세요.\n"
        "각 후보 정의가 현재 리포트에서 같은 표면어가 뜻하는 개념과 정확히 일치하는지 독립적으로 검토하세요.\n"
        "표면어가 같아도 정의에 등장하는 기관, 행위자, 제도가 현재 법안 문맥과 다르면 relevance를 low로 두세요.\n"
        "일반 독자에게 설명할 필요가 없는 평범한 말도 confidence 또는 relevance를 low로 두세요.\n"
        "후보에 없는 용어를 추가하지 말고, surface는 후보 term 또는 aliases 중 하나와 정확히 같은 표현만 사용하세요.\n"
        "확신할 수 없으면 rejected에 넣으세요. 아무 툴팁도 선택하지 않는 결과도 정상입니다.\n\n"
        "출력 규칙:\n"
        "- JSON 객체 하나만 출력하세요. 설명이나 코드펜스를 붙이지 마세요.\n"
        "- confidence와 relevance는 high 또는 low만 사용하세요.\n"
        "- definition은 출력하지 마세요. 최종 정의는 파이프라인이 후보 사전에서 가져옵니다.\n\n"
        "출력 스키마:\n"
        '{"tooltips":[{"term":"청문","surface":"청문 절차","reason":"현재 문맥의 처분 전 의견 진술 절차와 같은 개념","confidence":"high","relevance":"high"}],'
        '"rejected":[{"term":"의뢰인","reason":"후보 정의가 현재 법안의 의뢰인 개념과 다름"}]}\n\n'
        f"법안:\n{json.dumps({'bill_id': bill.get('bill_id'), 'bill_name': bill.get('bill_name')}, ensure_ascii=False)}\n\n"
        f"후보:\n{json.dumps(candidate_payload, ensure_ascii=False, indent=2)}\n\n"
        f"리포트 본문 시작\n{report_body.strip()}\n리포트 본문 끝\n"
    )


def apply_tooltip_decisions(
    report_body: str,
    candidates: list[LegalTermEntry],
    decisions_text: str,
) -> tuple[str, dict[str, Any]]:
    clean_body = _strip_term_tooltips(report_body).strip() + "\n"
    decisions = _parse_legal_term_tooltip_decisions(decisions_text, candidates)
    rendered = _apply_legal_term_tooltip_decisions(clean_body, decisions)
    rendered = _repair_term_tooltip_particles(rendered).strip() + "\n"
    if _strip_term_tooltips(rendered).strip() != clean_body.strip():
        raise RuntimeError("툴팁 적용 결과가 원본 리포트 본문을 변경했습니다.")
    _validate_report_body(rendered)
    return rendered, {
        "candidate_count": len(candidates),
        "applied_count": len(decisions),
        "terms": [decision.term for decision in decisions],
        "surfaces": [decision.surface for decision in decisions],
    }


def load_source_manifest_items(source_manifest: str) -> list[dict[str, Any]]:
    manifest_path = Path(source_manifest).expanduser().resolve()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    raw_items = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(raw_items, list):
        raise ValueError("source manifest에 items 배열이 없습니다.")

    items: list[dict[str, Any]] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict) or raw_item.get("status") != "success":
            continue
        report_path_value = raw_item.get("report_path")
        if not report_path_value:
            continue
        report_path = Path(str(report_path_value)).expanduser()
        if not report_path.is_absolute():
            report_path = manifest_path.parent / report_path
        if not report_path.exists():
            continue
        items.append(
            {
                "bill_id": str(raw_item.get("bill_id") or ""),
                "bill_name": str(raw_item.get("bill_name") or ""),
                "report_path": str(report_path.resolve()),
                "report_body": report_path.read_text(encoding="utf-8"),
            }
        )
    return [item for item in items if item["bill_id"] and item["report_body"].strip()]


def _fetch_bill_metadata(*, mode: str, bill_ids: list[str]) -> dict[str, dict[str, Any]]:
    if not bill_ids:
        return {}
    placeholders = ", ".join(["%s"] * len(bill_ids))
    conn = get_db_connection(mode=mode)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT bill_id, bill_name, brief_summary, summary_tags, gpt_summary
                FROM Bill
                WHERE bill_id IN ({placeholders})
                """,
                bill_ids,
            )
            return {str(row["bill_id"]): dict(row) for row in cur.fetchall()}
    finally:
        conn.close()


def fetch_bill_tooltip_targets(
    *,
    mode: str,
    limit: int,
    read_mode: str | None = None,
    target: str = "missing",
    source_manifest: str | None = None,
) -> list[dict[str, Any]]:
    db_mode = _resolve_read_mode(mode, read_mode)
    if source_manifest:
        manifest_items = load_source_manifest_items(source_manifest)[:limit]
        try:
            metadata = _fetch_bill_metadata(mode=db_mode, bill_ids=[item["bill_id"] for item in manifest_items])
        except Exception:
            if mode != "dry_run":
                raise
            metadata = {}
        return [{**metadata.get(item["bill_id"], {}), **item} for item in manifest_items]

    filters = ["gpt_summary IS NOT NULL", "gpt_summary != ''", "gpt_summary LIKE %s"]
    params: list[Any] = ["%## 쉬운 요약%"]
    if target == "missing":
        filters.append("gpt_summary NOT LIKE %s")
        params.append("%{{%:%}}%")
    where_clause = " AND ".join(filters)
    params.append(limit)
    conn = get_db_connection(mode=db_mode)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT bill_id, bill_name, brief_summary, summary_tags, gpt_summary
                FROM Bill
                WHERE {where_clause}
                ORDER BY propose_date DESC, bill_id DESC
                LIMIT %s
                """,
                params,
            )
            rows = list(cur.fetchall())
    finally:
        conn.close()
    return [
        {
            **dict(row),
            "report_body": f"# {row['bill_name']}\n\n{str(row['gpt_summary']).strip()}\n",
        }
        for row in rows
    ]


@dataclass(frozen=True)
class CodexBillTooltipAgent:
    model: str = DEFAULT_CODEX_MODEL

    def _runner(self) -> CodexBillReportAgent:
        return CodexBillReportAgent(model=self.model)

    def evaluate(
        self,
        *,
        bill: dict[str, Any],
        report_body: str,
        candidates: list[LegalTermEntry],
        output_path: Path,
        session_id: str | None = None,
    ) -> tuple[str, dict[str, Any]]:
        prompt = build_bill_tooltip_prompt(bill=bill, report_body=report_body, candidates=candidates)
        runner = self._runner()
        if session_id:
            command, stdin_text = runner.build_resume_command(
                session_id=session_id,
                prompt=prompt,
                output_path=str(output_path),
            )
        else:
            command, stdin_text = runner.build_command(prompt=prompt, output_path=str(output_path), ephemeral=False)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            command,
            input=stdin_text,
            capture_output=True,
            text=True,
            cwd=runner.workdir,
            env=runner.build_environment(),
            timeout=runner.timeout_seconds,
        )
        stdout_text = (proc.stdout or "").strip()
        if proc.returncode != 0:
            raise RuntimeError((proc.stderr or stdout_text or "Codex tooltip agent failed").strip())
        if not output_path.exists() and stdout_text:
            output_path.write_text(stdout_text, encoding="utf-8")
        if not output_path.exists() or not output_path.read_text(encoding="utf-8").strip():
            raise RuntimeError("Codex tooltip decision output is empty.")
        return output_path.read_text(encoding="utf-8"), {
            **_parse_codex_json_metadata(stdout_text),
            "prompt": prompt,
        }


def run_agentic_bill_tooltips(
    *,
    mode: str = "dry_run",
    limit: int = 5,
    output_dir: str = DEFAULT_TOOLTIP_OUTPUT_DIR,
    read_mode: str | None = None,
    codex_model: str | None = None,
    stop_on_error: bool = False,
    target: str = "missing",
    source_manifest: str | None = None,
    concurrency: int = 1,
    batch_session_size: int = DEFAULT_BATCH_SESSION_SIZE,
    failure_retry_attempts: int = 1,
    inspection: bool = False,
) -> dict[str, Any]:
    if limit < 1:
        raise ValueError("limit는 1 이상이어야 합니다.")
    if target not in TOOLTIP_TARGETS:
        raise ValueError("target은 missing 또는 all이어야 합니다.")
    if concurrency < 1:
        raise ValueError("concurrency는 1 이상이어야 합니다.")
    if batch_session_size < 1 or batch_session_size > MAX_BATCH_SESSION_SIZE:
        raise ValueError(f"batch_session_size는 1 이상 {MAX_BATCH_SESSION_SIZE} 이하여야 합니다.")
    if failure_retry_attempts < 0:
        raise ValueError("failure_retry_attempts는 0 이상이어야 합니다.")

    targets = fetch_bill_tooltip_targets(
        mode=mode,
        limit=limit,
        read_mode=read_mode,
        target=target,
        source_manifest=source_manifest,
    )
    output_root = Path(output_dir).expanduser().resolve()
    decisions_dir = output_root / "decisions"
    inspection_dir = output_root / "inspection" if inspection else None
    output_root.mkdir(parents=True, exist_ok=True)
    decisions_dir.mkdir(parents=True, exist_ok=True)
    if inspection_dir is not None:
        inspection_dir.mkdir(parents=True, exist_ok=True)
    agent = CodexBillTooltipAgent(model=codex_model or DEFAULT_CODEX_MODEL)
    items: list[dict[str, Any] | None] = [None] * len(targets)
    sessions: list[dict[str, Any]] = []
    started_at = datetime.now(timezone.utc)
    started_perf = time.perf_counter()

    def process_target(index: int, bill: dict[str, Any], session_id: str | None) -> tuple[dict[str, Any], str | None]:
        bill_id = str(bill.get("bill_id") or "")
        clean_body = _strip_term_tooltips(str(bill.get("report_body") or "")).strip() + "\n"
        candidates = build_legal_term_tooltip_entries(clean_body)
        base_item = {
            "bill_id": bill_id,
            "bill_name": bill.get("bill_name"),
            "candidate_count": len(candidates),
        }
        if not candidates:
            return {**base_item, "status": "skipped", "reason": "no_candidates", "db_upserted": False}, session_id

        last_error: Exception | None = None
        for attempt in range(failure_retry_attempts + 1):
            decision_path = decisions_dir / f"{_slugify_bill_id(bill_id)}.attempt{attempt + 1}.json"
            try:
                decisions_text, metadata = agent.evaluate(
                    bill=bill,
                    report_body=clean_body,
                    candidates=candidates,
                    output_path=decision_path,
                    session_id=session_id if attempt == 0 else None,
                )
                prompt_text = str(metadata.pop("prompt", ""))
                inspection_paths: dict[str, str] = {}
                if inspection_dir is not None:
                    prompt_path = inspection_dir / f"{_slugify_bill_id(bill_id)}.prompt.txt"
                    prompt_path.write_text(prompt_text, encoding="utf-8")
                    inspection_paths = {
                        "inspection_prompt_path": str(prompt_path),
                        "inspection_decision_path": str(decision_path),
                    }
                next_session_id = str(metadata.get("codex_thread_id") or session_id or "") or None
                rendered, details = apply_tooltip_decisions(clean_body, candidates, decisions_text)
                if details["applied_count"] == 0:
                    return {
                        **base_item,
                        **metadata,
                        **details,
                        **inspection_paths,
                        "status": "skipped",
                        "reason": "no_approved_tooltips",
                        "db_upserted": False,
                    }, next_session_id

                report_path = output_root / f"{_slugify_bill_id(bill_id)}.md"
                report_path.write_text(rendered, encoding="utf-8")
                db_upserted = False
                if mode != "dry_run":
                    payload = _build_db_summary_payload(bill, rendered)
                    update_bill_summary(
                        bill_id=bill_id,
                        brief_summary=payload.get("brief_summary"),
                        gpt_summary=payload.get("gpt_summary"),
                        summary_tags=payload.get("summary_tags"),
                        mode=_db_mode_for_execution(mode),
                        category=payload.get("category"),
                    )
                    db_upserted = True
                return {
                    **base_item,
                    **metadata,
                    **details,
                    **inspection_paths,
                    "status": "success",
                    "reason": "tooltips_applied",
                    "report_path": str(report_path),
                    "db_upserted": db_upserted,
                    "retry_count": attempt,
                }, next_session_id
            except Exception as exc:
                last_error = exc
        failed = {
            **base_item,
            "status": "failed",
            "reason": "tooltip_processing_failed",
            "error": str(last_error or "unknown tooltip failure"),
            "db_upserted": False,
            "retry_count": failure_retry_attempts,
        }
        if stop_on_error:
            raise RuntimeError(failed["error"])
        return failed, session_id

    def process_batch(batch_index: int, start_index: int, batch: list[dict[str, Any]]) -> dict[str, Any]:
        session_id: str | None = None
        started = time.perf_counter()
        for offset, bill in enumerate(batch):
            item, session_id = process_target(start_index + offset, bill, session_id)
            items[start_index + offset] = item
        return {
            "batch_index": batch_index,
            "bill_ids": [str(bill.get("bill_id") or "") for bill in batch],
            "codex_thread_id": session_id,
            "duration_seconds": round(time.perf_counter() - started, 3),
        }

    batches = [
        (batch_index, start_index, targets[start_index : start_index + batch_session_size])
        for batch_index, start_index in enumerate(range(0, len(targets), batch_session_size), start=1)
    ]
    if concurrency > 1 and len(batches) > 1:
        with ThreadPoolExecutor(max_workers=min(concurrency, len(batches))) as executor:
            futures = [executor.submit(process_batch, *batch) for batch in batches]
            for future in as_completed(futures):
                sessions.append(future.result())
    else:
        for batch in batches:
            sessions.append(process_batch(*batch))

    completed_items = [item for item in items if item is not None]
    finished_at = datetime.now(timezone.utc)
    usage_totals: dict[str, int] = {}
    for item in completed_items:
        usage = item.get("usage")
        if not isinstance(usage, dict):
            continue
        for key, value in usage.items():
            if isinstance(value, int):
                usage_totals[key] = usage_totals.get(key, 0) + value
    report = {
        "execution_mode": mode,
        "read_mode": _resolve_read_mode(mode, read_mode),
        "provider": "codex-agent",
        "model": codex_model or DEFAULT_CODEX_MODEL,
        "target": target,
        "source_manifest": source_manifest,
        "concurrency": concurrency,
        "batch_session_size": batch_session_size,
        "failure_retry_attempts": failure_retry_attempts,
        "output_dir": str(output_root),
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "stats": {
            "target_count": len(targets),
            "processed_count": len(completed_items),
            "success_count": sum(1 for item in completed_items if item["status"] == "success"),
            "skipped_count": sum(1 for item in completed_items if item["status"] == "skipped"),
            "failure_count": sum(1 for item in completed_items if item["status"] == "failed"),
            "db_upserted_count": sum(1 for item in completed_items if item.get("db_upserted")),
            "total_duration_seconds": round(time.perf_counter() - started_perf, 3),
            "usage_totals": usage_totals,
        },
        "items": completed_items,
        "sessions": sessions,
    }
    (output_root / "tooltip-manifest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    return report
