from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lawdigest_ai.db import get_db_connection, update_bill_title_if_current
from lawdigest_ai.processor.agentic_bill_report import (
    CodexBillReportAgent,
    _extract_json_object,
    _parse_codex_json_metadata,
    _resolve_read_mode,
    _validate_generated_title,
)

MAX_TITLE_BATCH_SIZE = 5
DEFAULT_TITLE_CODEX_MODEL = "gpt-5.4-mini"
RAW_SUMMARY_HEADING = re.compile(r"^제안이유\s*및\s*주요내용\s*")


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def is_raw_summary_copy_title(bill: dict[str, Any]) -> bool:
    gpt_summary = str(bill.get("gpt_summary") or "")
    if "## 쉬운 요약" not in gpt_summary or "## 주요 내용" not in gpt_summary:
        return False

    title = _normalize_text(bill.get("title")).rstrip(" .…")
    summary = RAW_SUMMARY_HEADING.sub("", _normalize_text(bill.get("summary")))
    return bool(title and summary.startswith(title))


def fetch_bill_title_regeneration_targets(
    *,
    mode: str,
    limit: int,
    read_mode: str | None = None,
) -> list[dict[str, Any]]:
    if limit < 1:
        raise ValueError("limit는 1 이상이어야 합니다.")

    db_mode = _resolve_read_mode(mode, read_mode)
    conn = get_db_connection(mode=db_mode)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    bill_id,
                    bill_name,
                    title,
                    summary,
                    gpt_summary,
                    propose_date
                FROM Bill
                WHERE title IS NOT NULL
                  AND title != ''
                  AND summary IS NOT NULL
                  AND summary != ''
                  AND gpt_summary LIKE %s
                  AND gpt_summary LIKE %s
                ORDER BY propose_date DESC, bill_id DESC
                """,
                ("%## 쉬운 요약%", "%## 주요 내용%"),
            )
            rows = list(cur.fetchall())
    finally:
        conn.close()

    targets: list[dict[str, Any]] = []
    for row in rows:
        if not is_raw_summary_copy_title(row):
            continue
        targets.append(row)
        if len(targets) == limit:
            break
    return targets


def build_bill_title_batch_prompt(bills: list[dict[str, Any]]) -> str:
    items = [
        {
            "bill_id": bill.get("bill_id"),
            "bill_name": bill.get("bill_name"),
            "summary": bill.get("summary"),
            "gpt_summary": bill.get("gpt_summary"),
        }
        for bill in bills
    ]
    return (
        "작업: Lawdigest 법안 카드에 표시할 제목만 생성하세요.\n"
        "기존 리포트 본문을 수정하거나 다시 작성하지 마세요. 제공된 summary와 gpt_summary를 근거로 제목만 작성하세요.\n\n"
        "제목 계약:\n"
        "- 각 title은 '[핵심 변경 목적/수단]을/를 위한 [정확한 bill_name]' 형식이어야 합니다.\n"
        "- 정확한 bill_name을 바꾸거나 줄이지 말고 title 끝에 그대로 붙이세요.\n"
        "- prefix는 1~80자의 짧은 명사형으로 쓰고 마침표, 물음표, 느낌표와 문장 종결 표현을 쓰지 마세요.\n"
        "- summary 또는 gpt_summary의 첫 문장을 그대로 복사하지 마세요.\n"
        "- 여러 변화가 있으면 가장 중요한 2~3개를 간결하게 묶으세요.\n\n"
        "출력 규칙:\n"
        "- JSON 객체 하나만 출력하고 설명이나 코드펜스를 붙이지 마세요.\n"
        "- titles 배열은 입력 순서와 같은 순서로 각 bill_id와 title을 정확히 한 번씩 포함하세요.\n"
        "- 다른 키는 만들지 마세요.\n\n"
        "출력 스키마:\n"
        '{"titles":[{"bill_id":"B001","title":"핵심 변화를 위한 예시법률안"}]}\n\n'
        f"입력:\n{json.dumps(items, ensure_ascii=False, indent=2, default=str)}"
    )


def parse_bill_title_batch_output(
    text: str,
    bills: list[dict[str, Any]],
) -> dict[str, str]:
    try:
        payload = json.loads(_extract_json_object(text))
    except (json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(f"제목 생성 결과가 올바른 JSON이 아닙니다: {exc}") from exc

    raw_titles = payload.get("titles") if isinstance(payload, dict) else None
    if not isinstance(raw_titles, list):
        raise RuntimeError("제목 생성 결과에 titles 배열이 없습니다.")

    expected_ids = [str(bill.get("bill_id") or "") for bill in bills]
    actual_ids = [str(item.get("bill_id") or "") for item in raw_titles if isinstance(item, dict)]
    if actual_ids != expected_ids or len(raw_titles) != len(bills):
        raise RuntimeError(
            f"제목 생성 결과의 bill_id 순서가 입력과 다릅니다: expected={expected_ids}, actual={actual_ids}"
        )

    parsed: dict[str, str] = {}
    for bill, item in zip(bills, raw_titles):
        if not isinstance(item, dict):
            raise RuntimeError("titles 항목은 JSON 객체여야 합니다.")
        bill_id = str(bill.get("bill_id") or "")
        title = str(item.get("title") or "").strip()
        _validate_generated_title(title, bill, required=True)
        if is_raw_summary_copy_title({**bill, "title": title}):
            raise RuntimeError(f"생성된 title이 원문 summary를 다시 복사했습니다: bill_id={bill_id}")
        parsed[bill_id] = title
    return parsed


@dataclass(frozen=True)
class CodexBillTitleAgent:
    model: str = DEFAULT_TITLE_CODEX_MODEL

    def write_titles_batch(
        self,
        bills: list[dict[str, Any]],
        *,
        output_path: str,
    ) -> dict[str, str]:
        if not bills or len(bills) > MAX_TITLE_BATCH_SIZE:
            raise ValueError(f"제목 배치는 1~{MAX_TITLE_BATCH_SIZE}건이어야 합니다.")

        report_agent = CodexBillReportAgent(model=self.model)
        prompt = build_bill_title_batch_prompt(bills)
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.unlink(missing_ok=True)
        command, stdin_text = report_agent.build_command(
            prompt=prompt,
            output_path=str(path),
            ephemeral=True,
        )
        proc = subprocess.run(
            command,
            input=stdin_text,
            capture_output=True,
            text=True,
            cwd=report_agent.workdir,
            env=report_agent.build_environment(),
            timeout=report_agent.timeout_seconds,
        )
        stdout_text = (proc.stdout or "").strip()
        stderr_text = (proc.stderr or "").strip()
        if proc.returncode != 0:
            raise RuntimeError(stderr_text or stdout_text or "Codex 제목 생성에 실패했습니다.")

        metadata = _parse_codex_json_metadata(stdout_text)
        if not path.exists() and stdout_text and not metadata.get("codex_event_count"):
            path.write_text(stdout_text, encoding="utf-8")
        if not path.exists() or path.stat().st_size == 0:
            raise RuntimeError("Codex 제목 생성 결과가 비어 있습니다.")
        return parse_bill_title_batch_output(path.read_text(encoding="utf-8"), bills)


def _gpt_summary_sha256(bill: dict[str, Any]) -> str:
    return hashlib.sha256(str(bill.get("gpt_summary") or "").encode("utf-8")).hexdigest()


def run_bill_title_regeneration(
    *,
    mode: str = "dry_run",
    limit: int = 5,
    output_dir: str = "/tmp/lawdigest-bill-title-regeneration",
    read_mode: str | None = None,
    codex_model: str | None = None,
    batch_size: int = MAX_TITLE_BATCH_SIZE,
    agent: Any | None = None,
) -> dict[str, Any]:
    if mode not in {"dry_run", "test", "prod"}:
        raise ValueError("mode는 dry_run, test, prod 중 하나여야 합니다.")
    if limit < 1:
        raise ValueError("limit는 1 이상이어야 합니다.")
    if batch_size < 1 or batch_size > MAX_TITLE_BATCH_SIZE:
        raise ValueError(f"batch_size는 1~{MAX_TITLE_BATCH_SIZE}여야 합니다.")

    targets = fetch_bill_title_regeneration_targets(mode=mode, read_mode=read_mode, limit=limit)
    output_root = Path(output_dir).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    resolved_model = codex_model or DEFAULT_TITLE_CODEX_MODEL
    title_agent = agent or CodexBillTitleAgent(model=resolved_model)
    items: list[dict[str, Any]] = []

    for start in range(0, len(targets), batch_size):
        batch = targets[start : start + batch_size]
        batch_path = output_root / f"batch-{start // batch_size + 1:04d}.json"
        try:
            generated = title_agent.write_titles_batch(batch, output_path=str(batch_path))
        except Exception as exc:
            for bill in batch:
                items.append(
                    {
                        "bill_id": bill.get("bill_id"),
                        "bill_name": bill.get("bill_name"),
                        "before_title": bill.get("title"),
                        "status": "failed",
                        "db_updated": False,
                        "gpt_summary_sha256": _gpt_summary_sha256(bill),
                        "error": str(exc),
                    }
                )
            continue

        for bill in batch:
            bill_id = str(bill.get("bill_id") or "")
            title = generated[bill_id]
            db_updated = False
            error: str | None = None
            if mode != "dry_run":
                db_updated = update_bill_title_if_current(
                    bill_id=bill_id,
                    title=title,
                    expected_title=str(bill.get("title") or ""),
                    mode="prod" if mode == "prod" else "test",
                )
                if not db_updated:
                    error = "조회 이후 title이 변경되어 조건부 UPDATE를 적용하지 않았습니다."
            items.append(
                {
                    "bill_id": bill_id,
                    "bill_name": bill.get("bill_name"),
                    "before_title": bill.get("title"),
                    "title": title,
                    "status": "success" if error is None else "failed",
                    "db_updated": db_updated,
                    "gpt_summary_sha256": _gpt_summary_sha256(bill),
                    **({"error": error} if error else {}),
                }
            )

    success_count = sum(item["status"] == "success" for item in items)
    failure_count = len(items) - success_count
    if not items:
        status = "empty"
    elif failure_count == 0:
        status = "success"
    elif success_count:
        status = "partial"
    else:
        status = "failed"
    result = {
        "status": status,
        "mode": mode,
        "model": resolved_model,
        "stats": {
            "target_count": len(targets),
            "success_count": success_count,
            "failure_count": failure_count,
        },
        "items": items,
    }
    (output_root / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return result
