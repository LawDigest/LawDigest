from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from lawdigest_ai.db import get_bill_table_columns, get_db_connection, update_bill_summary
from lawdigest_ai.processor.legal_term_glossary import build_legal_term_glossary_context

DEFAULT_OUTPUT_DIR = "/tmp/lawdigest-bill-agent-reports"
DEFAULT_CODEX_MODEL = os.getenv("BILL_AGENT_CODEX_MODEL", "gpt-5.4-mini")
DEFAULT_CODEX_BIN = os.getenv("CODEX_CLI_BIN", "codex")
DEFAULT_CODEX_TIMEOUT_SECONDS = int(os.getenv("BILL_AGENT_CODEX_TIMEOUT_SECONDS", "900"))
DEFAULT_AGENT_WORKDIR = os.getenv("BILL_AGENT_CODEX_WORKDIR", "/tmp")
DEFAULT_CODEX_HOME = os.getenv("BILL_AGENT_CODEX_HOME", "/home/ubuntu/.codex-report")
DEFAULT_BATCH_SESSION_SIZE = int(os.getenv("BILL_AGENT_BATCH_SESSION_SIZE", "5"))
MAX_BATCH_SESSION_SIZE = 5
CODEX_AUTH_FILES = ("auth.json", ".credentials.json", "installation_id")
CODEX_SYSTEM_SKILL_NAMES = ("imagegen", "openai-docs", "plugin-creator", "skill-creator", "skill-installer")
REPORT_CODEX_CONFIG_BEGIN = "# BEGIN Lawdigest bill report agent managed skills"
REPORT_CODEX_CONFIG_END = "# END Lawdigest bill report agent managed skills"

PASSED_RESULT_TERMS = ("원안가결", "수정가결", "가결")
PASSED_STAGE_TERMS = ("공포", "본회의 의결")
EXCLUDED_RESULT_TERMS = ("폐기", "철회", "부결", "임기만료")
REPORT_MODES = ("auto", "summary", "deep_report")
TARGETS = ("passed", "pending", "all")
EFFECTIVE_AGENT_TOOL_AUDIT = {
    "source_run": "/tmp/lawdigest-bill-agent-reports/default-prod-five-20260704234548",
    "effective_prefetch": (
        "open_assembly.fetch_bill_detail",
        "open_assembly.fetch_bill_summary",
        "open_assembly.fetch_rows(BILLJUDGE)",
        "law.go.kr.search_current_law",
        "law.go.kr.fetch_current_law_articles",
    ),
    "called_but_excluded_from_default": (
        "korean-law.search_law",
        "korean-law.get_law_text",
        "korean-law.legal_analysis",
        "korean-law.legal_research",
        "korean-law.execute_tool",
        "open-assembly.discover_apis",
        "web_search",
        "command_execution",
    ),
    "not_effective_in_sample": (
        "assembly-api.*",
        "korean-stats.*",
        "open-assembly.get_bill_proposers",
        "open-assembly.get_vote_results",
    ),
}
MCP_APPROVED_TOOLS = {
    "korean-stats": (
        "search_statistics",
        "get_statistics_list",
        "get_statistics_data",
        "compare_statistics",
        "analyze_time_series",
        "get_table_info",
        "quick_stats",
        "quick_trend",
        "quick_rank",
        "explain_statistic",
        "fetch_kosis_excel",
        "chain_region_brief",
        "chain_compare_regions",
        "chain_policy_indicator",
    ),
    "korean-law": (
        "search_law",
        "get_law_text",
        "get_annexes",
        "legal_research",
        "legal_analysis",
        "discover_tools",
        "execute_tool",
        "get_legal_term_kb",
        "get_legal_term_detail",
        "get_daily_term",
        "get_daily_to_legal",
        "get_legal_to_daily",
        "get_term_articles",
        "search_decisions",
        "get_decision_text",
    ),
    "open-assembly": (
        "search_bills",
        "get_bill_detail",
        "get_member_info",
        "get_vote_results",
        "get_bill_review",
        "get_bill_proposers",
        "get_member_votes",
        "get_committee_members",
        "get_pending_bills",
        "get_plenary_agenda",
        "get_bill_committee_review",
        "get_bill_summary",
        "analyze_legislator",
        "get_party_cohesion",
        "search_nars_reports",
        "search_petitions",
        "get_schedule",
        "search_hearings",
        "discover_apis",
        "query_assembly",
    ),
    "assembly-api": (
        "assembly_member",
        "assembly_bill",
        "assembly_session",
        "assembly_org",
        "discover_apis",
        "query_assembly",
        "bill_detail",
        "committee_detail",
        "petition_detail",
        "research_data",
    ),
}
INSPECTION_ACTION_ITEM_TYPES = {
    "function_call",
    "tool_call",
    "mcp_tool_call",
    "web_search",
    "command_execution",
}
INSPECTION_OUTPUT_ITEM_TYPES = INSPECTION_ACTION_ITEM_TYPES | {
    "function_call_output",
    "tool_call_output",
}


class BillReportGenerationError(RuntimeError):
    def __init__(self, message: str, *, details: dict[str, Any]):
        super().__init__(message)
        self.details = details


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _toml_array(values: list[str]) -> str:
    return "[" + ", ".join(_toml_string(value) for value in values) + "]"


def _toml_inline_table(values: dict[str, str]) -> str:
    if not values:
        return "{}"
    return "{ " + ", ".join(f"{key} = {_toml_string(value)}" for key, value in values.items()) + " }"


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _iter_skill_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.glob("*/SKILL.md") if path.is_file())


def _discover_skills_to_disable(*, codex_home: Path, workdir: str) -> list[Path]:
    roots: list[Path] = [
        Path.home() / ".agents" / "skills",
        Path.home() / ".codex" / "skills",
        Path.home() / ".codex" / "superpowers" / "skills",
        Path("/etc/codex/skills"),
        codex_home / "skills" / ".system",
    ]

    current = Path(workdir).expanduser().resolve()
    for directory in (current, *current.parents):
        roots.append(directory / ".agents" / "skills")
        roots.append(directory / ".codex" / "skills")
        if (directory / ".git").exists():
            break

    disabled: dict[str, Path] = {}
    report_skill_root = codex_home / "skills"
    for root in roots:
        for skill_file in _iter_skill_files(root.expanduser()):
            if _is_relative_to(skill_file, report_skill_root) and not _is_relative_to(
                skill_file, report_skill_root / ".system"
            ):
                continue
            disabled[str(skill_file.resolve())] = skill_file.resolve()
    for skill_name in CODEX_SYSTEM_SKILL_NAMES:
        skill_file = (report_skill_root / ".system" / skill_name / "SKILL.md").resolve()
        disabled[str(skill_file)] = skill_file
    return list(disabled.values())


def _build_report_codex_config_block(disabled_skill_files: list[Path]) -> str:
    lines = [REPORT_CODEX_CONFIG_BEGIN]
    for skill_file in disabled_skill_files:
        lines.extend((
            "[[skills.config]]",
            f"path = {_toml_string(str(skill_file))}",
            "enabled = false",
            "",
        ))
    lines.append(REPORT_CODEX_CONFIG_END)
    return "\n".join(lines).rstrip() + "\n"


def _write_report_codex_config(*, codex_home: Path, workdir: str) -> None:
    config_path = codex_home / "config.toml"
    managed_block = _build_report_codex_config_block(
        _discover_skills_to_disable(codex_home=codex_home, workdir=workdir)
    )
    existing = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    pattern = re.compile(
        rf"{re.escape(REPORT_CODEX_CONFIG_BEGIN)}.*?{re.escape(REPORT_CODEX_CONFIG_END)}\n?",
        re.DOTALL,
    )
    if pattern.search(existing):
        updated = pattern.sub(managed_block, existing)
    else:
        separator = "\n" if existing and not existing.endswith("\n") else ""
        updated = f"{existing}{separator}{managed_block}"
    if updated != existing:
        config_path.write_text(updated, encoding="utf-8")


def _slugify_bill_id(value: Any) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value or "bill").strip())
    return slug.strip("_") or "bill"


def _parse_codex_json_metadata(stdout_text: str) -> dict[str, Any]:
    thread_id: str | None = None
    usage: dict[str, Any] | None = None
    event_count = 0
    for line in stdout_text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        event_count += 1
        if event.get("type") == "thread.started":
            thread_id = event.get("thread_id")
        if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
            usage = event["usage"]
    return {
        "codex_thread_id": thread_id,
        "codex_event_count": event_count,
        "token_usage_available": usage is not None,
        "usage": usage,
    }


def _preview(value: Any, limit: int = 1200) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, ensure_ascii=False, default=str)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return None
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _build_bill_payload(bill: Dict[str, Any]) -> dict[str, Any]:
    return {
        "bill_id": bill.get("bill_id"),
        "bill_number": bill.get("bill_number"),
        "bill_name": bill.get("bill_name"),
        "bill_result": bill.get("bill_result"),
        "stage": bill.get("stage"),
        "committee": bill.get("committee"),
        "propose_date": str(bill.get("propose_date") or ""),
        "proposers": bill.get("proposers"),
        "summary": bill.get("summary"),
        "bill_link": bill.get("bill_link"),
        "bill_pdf_url": bill.get("bill_pdf_url"),
    }


def _compact_evidence_value(value: Any, *, limit: int = 2500) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        text = re.sub(r"\s+", " ", value).strip()
        if len(text) > limit:
            return text[: limit - 1] + "…"
        return text
    if isinstance(value, (int, float, bool)):
        return value
    return str(value)


def _compact_evidence_row(row: dict[str, Any] | None, *, text_limit: int = 2500) -> dict[str, Any]:
    if not row:
        return {}
    compact: dict[str, Any] = {}
    for key, value in row.items():
        compact_value = _compact_evidence_value(value, limit=text_limit)
        if compact_value not in (None, ""):
            compact[key] = compact_value
    return compact


def _resolve_assembly_api_key() -> str | None:
    return os.getenv("ASSEMBLY_API_KEY") or os.getenv("APIKEY_billsInfo") or os.getenv("APIKEY_status")


def _build_open_assembly_client(api_key: str | None = None) -> Any | None:
    resolved_api_key = api_key or _resolve_assembly_api_key()
    if not resolved_api_key:
        return None
    try:
        import requests
        from lawdigest_data.bills.open_assembly import OpenAssemblyBillClient
    except Exception:
        return None
    return OpenAssemblyBillClient(requests.Session(), resolved_api_key)


def _first_text(*values: Any) -> str | None:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return None


def _split_proposal_summary(summary_text: str | None) -> dict[str, Any]:
    text = re.sub(r"\s+", " ", str(summary_text or "")).strip()
    if not text:
        return {}
    normalized = re.sub(r"^제안이유\s*및\s*주요내용\s*", "", text).strip()
    return {
        "proposal_reason_and_major_content": _compact_evidence_value(normalized, limit=6000),
        "raw_heading": "제안이유 및 주요내용" if normalized != text else None,
    }


def _extract_target_law_names(bill_name: str | None) -> list[str]:
    name = str(bill_name or "").strip()
    if not name:
        return []
    patterns = (
        r"(.+?법)\s+일부개정법률안",
        r"(.+?법)\s+전부개정법률안",
        r"(.+?법)\s+폐지법률안",
    )
    for pattern in patterns:
        match = re.search(pattern, name)
        if match:
            return [match.group(1).strip()]
    if name.endswith("법안") and "개정" not in name:
        return []
    return []


def _article_ref_to_jo(article_ref: str) -> str | None:
    match = re.search(r"제\s*(\d+)\s*조(?:의\s*(\d+))?", article_ref)
    if not match:
        return None
    article = int(match.group(1))
    branch = int(match.group(2) or 0)
    return f"{article:04d}{branch:02d}"


def _extract_article_refs(*texts: Any, limit: int = 8) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    seen: set[str] = set()
    combined = " ".join(str(text or "") for text in texts)
    for match in re.finditer(r"제\s*\d+\s*조(?:의\s*\d+)?", combined):
        label = re.sub(r"\s+", "", match.group(0))
        if label in seen:
            continue
        jo = _article_ref_to_jo(label)
        if jo:
            refs.append({"label": label, "JO": jo})
            seen.add(label)
        if len(refs) >= limit:
            break
    return refs


def _find_first_nested(value: Any, keys: tuple[str, ...]) -> Any:
    if isinstance(value, dict):
        for key in keys:
            if key in value:
                return value[key]
        for nested in value.values():
            found = _find_first_nested(nested, keys)
            if found is not None:
                return found
    if isinstance(value, list):
        for item in value:
            found = _find_first_nested(item, keys)
            if found is not None:
                return found
    return None


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _build_law_api_client() -> Any | None:
    oc = os.getenv("LAW_OC")
    if not oc:
        return None
    try:
        import requests
    except Exception:
        return None
    return requests.Session(), oc


def _search_current_law(law_name: str, *, client: Any | None = None) -> dict[str, Any]:
    session_and_oc = client or _build_law_api_client()
    if session_and_oc is None:
        return {"law_name": law_name, "status": "law_api_unavailable"}
    session, oc = session_and_oc
    response = session.get(
        "https://www.law.go.kr/DRF/lawSearch.do",
        params={"OC": oc, "target": "law", "type": "JSON", "query": law_name, "display": 3},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    rows = _as_list(_find_first_nested(payload, ("law", "법령", "법령검색")))
    candidates: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        law_title = _first_text(row.get("법령명한글"), row.get("법령명_한글"), row.get("법령명"))
        if not law_title:
            continue
        candidates.append({
            "law_name": law_title,
            "law_id": _first_text(row.get("법령ID"), row.get("ID")),
            "mst": _first_text(row.get("법령일련번호"), row.get("MST"), row.get("lsi_seq")),
            "promulgation_date": _first_text(row.get("공포일자")),
            "effective_date": _first_text(row.get("시행일자")),
        })
    return {"law_name": law_name, "status": "found" if candidates else "not_found", "candidates": candidates[:3]}


def _fetch_current_law_article(mst: str | None, article_ref: dict[str, str], *, client: Any | None = None) -> dict[str, Any]:
    if not mst:
        return {**article_ref, "status": "missing_law_mst"}
    session_and_oc = client or _build_law_api_client()
    if session_and_oc is None:
        return {**article_ref, "status": "law_api_unavailable"}
    session, oc = session_and_oc
    response = session.get(
        "https://www.law.go.kr/DRF/lawService.do",
        params={"OC": oc, "target": "lawjosub", "type": "JSON", "MST": mst, "JO": article_ref["JO"]},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    article_text = _find_first_nested(payload, ("조문내용", "조문내용문자열", "조문"))
    return {
        **article_ref,
        "status": "found" if article_text else "not_found",
        "text": _compact_evidence_value(article_text, limit=1800),
    }


def _row_matches_bill(row: dict[str, Any], *, bill_id: str | None, bill_no: str | None) -> bool:
    row_bill_id = _first_text(row.get("BILL_ID"), row.get("bill_id"))
    row_bill_no = _first_text(row.get("BILL_NO"), row.get("bill_no"))
    if bill_id and row_bill_id:
        return row_bill_id == bill_id
    if bill_no and row_bill_no:
        return row_bill_no == bill_no
    return False


def _build_cost_estimate_evidence(rows: list[dict[str, Any]]) -> dict[str, Any]:
    keywords = ("비용추계", "재정", "예산", "미첨부", "첨부", "소요비용", "재원")
    matches: list[dict[str, Any]] = []
    for row in rows:
        for key, value in row.items():
            text = str(value or "").strip()
            if text and any(keyword in text for keyword in keywords):
                matches.append({"field": key, "text": _compact_evidence_value(text, limit=1200)})
    return {"status": "found" if matches else "not_found", "matches": matches[:8]}


def _bill_is_passed(bill: dict[str, Any]) -> bool:
    result = str(bill.get("bill_result") or "")
    stage = str(bill.get("stage") or "")
    excluded = any(term in result for term in EXCLUDED_RESULT_TERMS)
    if excluded:
        return False
    return any(term in result for term in PASSED_RESULT_TERMS) or any(term in stage for term in PASSED_STAGE_TERMS)


def _resolve_report_mode(report_mode: str, bill: dict[str, Any]) -> str:
    if report_mode not in REPORT_MODES:
        raise ValueError("report_mode은 auto, summary, deep_report 중 하나여야 합니다.")
    return "deep_report"


def build_bill_report_evidence(bill: Dict[str, Any], *, report_mode: str = "auto") -> dict[str, Any]:
    resolved_mode = _resolve_report_mode(report_mode, bill)
    evidence: dict[str, Any] = {
        "report_mode": resolved_mode,
        "db_bill": _build_bill_payload(bill),
        "prefetch_plan": EFFECTIVE_AGENT_TOOL_AUDIT,
        "open_assembly": {},
        "bill_text": {},
        "current_law": {},
        "committee_materials": {},
        "cost_estimate": {},
        "prefetch_errors": [],
    }

    client = _build_open_assembly_client()
    if client is None:
        evidence["prefetch_errors"].append("open_assembly_client_unavailable")
        return evidence

    bill_id = _first_text(bill.get("bill_id"))
    bill_no = _first_text(bill.get("bill_number"))
    try:
        detail_row = client.fetch_bill_detail(bill_id) if bill_id else None
        evidence["open_assembly"]["detail"] = _compact_evidence_row(detail_row)
        bill_no = _first_text(
            bill_no,
            detail_row.get("BILL_NO") if isinstance(detail_row, dict) else None,
        )
    except Exception as exc:
        evidence["prefetch_errors"].append(f"fetch_bill_detail_failed: {exc}")

    if not bill_no:
        return evidence

    summary_row: dict[str, Any] | None = None
    try:
        summary_row = client.fetch_bill_summary(bill_no)
        evidence["open_assembly"]["summary"] = _compact_evidence_row(summary_row)
    except Exception as exc:
        evidence["prefetch_errors"].append(f"summary_prefetch_failed: {exc}")

    summary_text = _first_text(
        summary_row.get("SUMMARY") if isinstance(summary_row, dict) else None,
        bill.get("summary"),
    )
    target_law_names = _extract_target_law_names(_first_text(bill.get("bill_name"), detail_row.get("BILL_NM") if isinstance(detail_row, dict) else None))
    article_refs = _extract_article_refs(summary_text)
    evidence["bill_text"] = {
        **_split_proposal_summary(summary_text),
        "target_law_names": target_law_names,
        "mentioned_articles": article_refs,
        "bill_pdf_url": _first_text(
            bill.get("bill_pdf_url"),
            detail_row.get("BILL_PDF_URL") if isinstance(detail_row, dict) else None,
            detail_row.get("PDF_LINK_URL") if isinstance(detail_row, dict) else None,
        ),
        "bill_link": _first_text(
            bill.get("bill_link"),
            detail_row.get("LINK_URL") if isinstance(detail_row, dict) else None,
        ),
    }

    law_client = _build_law_api_client()
    current_law_items: list[dict[str, Any]] = []
    for law_name in target_law_names[:2]:
        try:
            law_search = _search_current_law(law_name, client=law_client)
            candidates = law_search.get("candidates") if isinstance(law_search, dict) else None
            mst = None
            if isinstance(candidates, list) and candidates:
                mst = candidates[0].get("mst")
            articles = [
                _fetch_current_law_article(str(mst) if mst else None, article_ref, client=law_client)
                for article_ref in article_refs[:5]
            ]
            current_law_items.append({**law_search, "articles": articles})
        except Exception as exc:
            evidence["prefetch_errors"].append(f"current_law_prefetch_failed: {law_name}: {exc}")
            current_law_items.append({"law_name": law_name, "status": "failed"})
    evidence["current_law"] = {
        "target_law_names": target_law_names,
        "mentioned_articles": article_refs,
        "laws": current_law_items,
    }

    review_rows: list[dict[str, Any]] = []
    try:
        raw_review_rows = client.fetch_rows("BILLJUDGE", {"BILL_NO": bill_no}, all_pages=False, page_size=10)
        review_rows = [
            _compact_evidence_row(row)
            for row in raw_review_rows
            if isinstance(row, dict) and _row_matches_bill(row, bill_id=bill_id, bill_no=bill_no)
        ][:5]
        evidence["open_assembly"]["review"] = review_rows
    except Exception as exc:
        evidence["prefetch_errors"].append(f"review_prefetch_failed: {exc}")

    evidence["committee_materials"] = {
        "review_rows": review_rows,
        "status": "found" if review_rows else "not_found",
        "note": "BILLJUDGE rows are included only when BILL_ID or BILL_NO matches the target bill.",
    }
    evidence["cost_estimate"] = _build_cost_estimate_evidence([
        row
        for row in (
            _compact_evidence_row(detail_row if isinstance(detail_row, dict) else None),
            _compact_evidence_row(summary_row if isinstance(summary_row, dict) else None),
            *review_rows,
        )
        if row
    ])

    return evidence


def _sanitize_codex_event(event: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {"type": event.get("type")}
    if event.get("thread_id"):
        sanitized["thread_id"] = event.get("thread_id")
    if isinstance(event.get("usage"), dict):
        sanitized["usage"] = event["usage"]

    item = event.get("item")
    if isinstance(item, dict):
        item_type = item.get("type")
        sanitized["item_type"] = item_type
        for key in (
            "name",
            "call_id",
            "status",
            "server",
            "server_name",
            "mcp_server",
            "tool",
            "tool_name",
            "function",
            "function_name",
            "command",
            "query",
        ):
            if item.get(key) is not None:
                sanitized[key] = item.get(key)
        if item_type in INSPECTION_ACTION_ITEM_TYPES:
            sanitized["arguments_preview"] = _preview(
                item.get("arguments") or item.get("input") or item.get("args") or item.get("params")
            )
        if item_type in INSPECTION_OUTPUT_ITEM_TYPES:
            sanitized["output_preview"] = _preview(
                item.get("output") or item.get("result") or item.get("content") or item.get("text")
            )

    message = event.get("message")
    if isinstance(message, dict):
        sanitized["message_role"] = message.get("role")
        sanitized["message_preview"] = _preview(message.get("content"), limit=500)

    return {key: value for key, value in sanitized.items() if value is not None}


def _parse_codex_inspection_events(stdout_text: str) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    tool_calls: list[dict[str, Any]] = []
    for line in stdout_text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        sanitized = _sanitize_codex_event(event)
        events.append(sanitized)
        if sanitized.get("item_type") in INSPECTION_ACTION_ITEM_TYPES or sanitized.get("name"):
            tool_calls.append({
                key: sanitized[key]
                for key in (
                    "type",
                    "item_type",
                    "name",
                    "server",
                    "server_name",
                    "mcp_server",
                    "tool",
                    "tool_name",
                    "function",
                    "function_name",
                    "command",
                    "query",
                    "call_id",
                    "status",
                    "arguments_preview",
                    "output_preview",
                )
                if key in sanitized
            })
    return {"events": events, "tool_calls": tool_calls}


def _extract_evidence_section(report_body: str) -> list[str]:
    evidence_body = _markdown_section_body(report_body, "## 확인한 근거")
    if evidence_body == report_body:
        return []
    evidence: list[str] = []
    for line in evidence_body.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            evidence.append(stripped[2:].strip())
    return evidence


def _write_inspection_artifacts(
    *,
    inspection_dir: Path,
    bill: Dict[str, Any],
    prompt: str,
    command: list[str],
    stdout_text: str,
    stderr_text: str,
    report_path: Path,
    details: dict[str, Any],
    validation: dict[str, Any],
) -> dict[str, str]:
    bill_id = _slugify_bill_id(bill.get("bill_id"))
    inspection_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = inspection_dir / f"{bill_id}.prompt.txt"
    events_path = inspection_dir / f"{bill_id}.codex-events.jsonl"
    inspection_path = inspection_dir / f"{bill_id}.inspection.json"

    prompt_path.write_text(prompt, encoding="utf-8")
    event_summary = _parse_codex_inspection_events(stdout_text)
    with events_path.open("w", encoding="utf-8") as handle:
        for event in event_summary["events"]:
            handle.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")

    report_body = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    command_summary = [
        "<redacted-env>" if arg.startswith("mcp_servers.") and ".env=" in arg else arg
        for arg in command
    ]
    inspection = {
        "schema_version": 1,
        "mode": "inspection",
        "bill": _build_bill_payload(bill),
        "prompt": {
            "path": str(prompt_path),
            "sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "character_count": len(prompt),
        },
        "agent": {
            "command_summary": command_summary,
            "codex_thread_id": details.get("codex_thread_id"),
            "event_count": details.get("codex_event_count"),
            "tool_calls": event_summary["tool_calls"],
            "usage": details.get("usage"),
            "stderr_preview": _preview(stderr_text),
        },
        "behavior_log": [
            {
                "step": "build_prompt",
                "summary": "입력 법안 payload와 법제처 용어 컨텍스트를 합쳐 작성 프롬프트를 구성했습니다.",
            },
            {
                "step": "run_codex_agent",
                "summary": "Codex CLI를 read-only sandbox와 임시 MCP 설정으로 실행했습니다.",
            },
            {
                "step": "write_markdown_report",
                "summary": "에이전트의 마지막 응답을 Markdown 리포트 파일로 저장했습니다.",
            },
            {
                "step": "validate_report",
                "summary": validation["summary"],
            },
        ],
        "evidence": {
            "reported_sources": _extract_evidence_section(report_body),
            "note": "이 항목은 최종 Markdown의 확인한 근거 섹션에서 추출한 사용자 표시용 근거입니다. 도구 원문 전체가 아니라 감사용 요약입니다.",
        },
        "validation": validation,
        "outputs": {
            "report_path": str(report_path),
            "inspection_path": str(inspection_path),
            "events_path": str(events_path),
            "prompt_path": str(prompt_path),
        },
        "runtime": {
            "started_at": details.get("started_at"),
            "finished_at": details.get("finished_at"),
            "duration_seconds": details.get("duration_seconds"),
            "exit_code": details.get("exit_code"),
            "output_bytes": details.get("output_bytes"),
        },
    }
    inspection_path.write_text(
        json.dumps(inspection, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return {
        "inspection_path": str(inspection_path),
        "inspection_events_path": str(events_path),
        "inspection_prompt_path": str(prompt_path),
    }


def _normalize_usage_meter(usage_meter: dict[str, Any] | None) -> dict[str, Any] | None:
    if not usage_meter:
        return None
    normalized: dict[str, Any] = {}
    for key in ("weekly", "five_hour"):
        raw_meter = usage_meter.get(key)
        if not isinstance(raw_meter, dict):
            continue
        meter = {
            field: raw_meter[field]
            for field in ("before_percent", "after_percent")
            if raw_meter.get(field) is not None
        }
        before = meter.get("before_percent")
        after = meter.get("after_percent")
        if isinstance(before, (int, float)) and isinstance(after, (int, float)):
            meter["delta_percent"] = round(after - before, 3)
        if meter:
            normalized[key] = meter
    return normalized or None


def _db_mode_for_execution(mode: str) -> str:
    return "prod" if mode == "prod" else "test"


def _resolve_read_mode(mode: str, read_mode: str | None) -> str:
    if read_mode:
        return read_mode
    return _db_mode_for_execution(mode)


def build_bill_report_prompt(
    bill: Dict[str, Any],
    *,
    report_mode: str = "auto",
    evidence: dict[str, Any] | None = None,
) -> str:
    payload = _build_bill_payload(bill)
    payload_text = json.dumps(payload, ensure_ascii=False, default=str)
    legal_term_context = build_legal_term_glossary_context(payload_text)
    evidence_payload = evidence or {
        "report_mode": _resolve_report_mode(report_mode, bill),
        "db_bill": payload,
        "prefetch_plan": EFFECTIVE_AGENT_TOOL_AUDIT,
        "open_assembly": {},
        "prefetch_errors": ["prefetch_not_run"],
    }
    mode_contract = (
        "리포트 모드: deep_report\n"
        "- 모든 법안은 처리 상태와 관계없이 긴 버전 리포트로 작성합니다.\n"
        "- 아직 통과되지 않았거나 막 접수된 법안은 제도가 확정된 것처럼 말하지 말고, 법안이 제안하는 변화와 앞으로 볼 점을 중심으로 설명하세요.\n"
        "- 여러 제도가 함께 바뀌는 복합 개정안은 최종 리포트가 6,000~8,000자 안팎이 되도록 근거, 영향, 예외를 충분히 설명하세요.\n"
        "- `## 무엇이 달라지나`는 가능하면 4~6개 변화 묶음으로 나누세요.\n"
    )
    return (
        "당신은 Lawdigest의 법안 리포트 작성자입니다.\n"
        "아래 입력은 Lawdigest가 사전에 수집한 deterministic evidence packet입니다. "
        "추가 도구 호출, 웹 검색, 셸 명령 실행을 하지 말고 제공된 evidence 안에서만 사실관계를 사용하세요. "
        "출력은 내부 조사 로그가 아니라 사용자에게 보여줄 최종 법안 리포트여야 합니다.\n\n"
        f"{mode_contract}\n"
        "근거 사용 원칙:\n"
        "- bill_text, current_law, committee_materials, cost_estimate, open_assembly.detail, summary, review와 DB 값을 우선 사용하세요.\n"
        "- lifecycle, 현재 심사 단계, 처리 상태처럼 시간이 지나며 바뀌는 정보는 리포트 본문 근거로 쓰지 마세요.\n"
        "- evidence가 비어 있거나 prefetch_errors가 있으면 빈 근거를 지어내지 말고, DB에 있는 원문 요약과 법안 기본정보 범위에서만 설명하세요.\n"
        "- assembly-api, korean-stats, web_search 결과는 기본 evidence에 없으므로 언급하지 마세요.\n"
        "- 법제처 용어 사전 컨텍스트는 어려운 법률·행정용어를 한 번만 쉽게 풀 때 사용하세요.\n\n"
        "출력 형식:\n"
        "# 법안명\n"
        "## 쉬운 요약\n"
        "- 법안이 무엇을 바꾸는지 5개 불릿으로 설명하세요. 토스 앱처럼 쉬운 말로 충분히 설명하는 것이 목표입니다.\n"
        "- 짧다는 뜻은 문장을 쉽게 쓰는 것이지 정보량을 줄이는 것이 아닙니다.\n"
        "- 본회의 표결수, 현재 심사 단계, 공포일 같은 상태값은 프론트엔드 데이터가 따로 보여주므로 요약 본문에 쓰지 마세요.\n"
        "- 법안의 처리 상태를 요약 첫 문장으로 앞세우지 마세요. 미확정 상태 안내처럼 상태를 먼저 말하지 말고, "
        "`소상공인의 정보보호 부담을 줄이기 위한 법률 개정안이에요`처럼 법안이 하려는 일을 먼저 설명하세요.\n"
        "- 첫 불릿은 가능하면 `- ...하기 위한 법률 개정안이에요.` 형태로 목적을 바로 말하세요.\n"
        "## 주요 내용\n"
        "- 여러 제도가 함께 바뀌는 법안이면 5~7개 항목을 쓰세요.\n"
        "- 각 항목은 반드시 `**항목 제목**: 쉬운 설명` 형식으로 쓰세요.\n"
        "- 콜론 앞 핵심 내용은 반드시 Markdown 볼드체로 나타내세요. 예: `**부당한 표시·광고 제한**: 허위·과장 등 소비자를 오도할 수 있는 표현을 규제해요.`\n"
        "- `핵심:` 또는 `설명:` 같은 메타 라벨을 그대로 출력하지 마세요.\n"
        "## 왜 나왔나\n"
        "- 제안 이유와 정책 배경을 사용자 관점에서 3~4문장으로 설명하세요.\n"
        "## 무엇이 달라지나\n"
        "- 현행법과 달라지는 점을 구체적으로 쓰되, 각 변화 묶음은 반드시 제목, 원문 요약 문단, 설명/풀이 불릿 순서로 쓰세요.\n"
        "- 각 변화 묶음은 반드시 `### 1) 제목`, `### 2) 제목`처럼 번호 헤딩으로 시작하세요.\n"
        "- 가능하면 4~6개 변화 묶음으로 나누고, 한 묶음에 여러 제도를 억지로 합치지 마세요.\n"
        "- 제목은 설명문이 아니라 짧은 명사형 항목명으로 쓰세요.\n"
        "- 예를 들어 `허위개발정보 유포를 금지하는 조문을 새로 둔다`가 아니라 `허위개발정보 유포를 금지하는 조문 신설`로 쓰세요.\n"
        "- `인터넷 표시·광고의 필수정보와 부당한 표시를 제한한다`가 아니라 `인터넷 표시·광고의 필수정보와 부당한 표시를 제한`으로 쓰세요.\n"
        "- `벌칙·과태료 체계 개정과 집행주체 확충`처럼 행정문서식 표현은 피하고, `허위정보·부당광고 위반 시 제재 강화`처럼 사용자가 바로 이해하는 말로 풀어 쓰세요.\n"
        "- 번호 헤딩 다음에는 불릿이 아닌 일반 문단으로 원문 조문 변화의 요약을 1문단 쓰세요. 원문 요약 문단은 2문장으로 쓰세요.\n"
        "- 그 아래에 필요한 설명/풀이를 Markdown 불릿(`- ...`)으로 붙이세요. 각 변화 묶음마다 2~3개 불릿을 쓰세요.\n"
        "- 불릿만으로 변화 묶음을 시작하지 마세요.\n"
        "- 청문 규정, 과태료, 위임·위탁, 조문 체계처럼 일반 사용자가 모를 법한 법률·행정 용어는 괄호로 끼워 넣지 마세요.\n"
        "- `제23조(청문)`처럼 출처식 괄호 표기를 본문에 옮기지 마세요. 본문에 청문을 언급해야 하면 별도 `청문 규정:` 불릿으로 설명하세요.\n"
        "- `- 실제 용어명으로 시작하는 설명 불릿`은 어려운 법률·행정 용어가 있을 때만 중간에 붙이세요.\n"
        "- 용어 설명과 쉬운 풀이 문장은 반드시 Markdown 불릿(`- ...`)으로 쓰세요.\n"
        "- 첫 문장에 `원문 요약:` 같은 메타 라벨을 붙이지 말고 바로 조문 변화 문장을 쓰세요.\n"
        "- 용어 설명 불릿은 `용어 설명:`이나 `법령 체계:` 같은 메타 라벨을 쓰지 말고, 반드시 실제 용어명으로 시작하세요. 예: `청문 규정:`, `과태료:`, `위임·위탁:`\n"
        "- 쉬운 풀이 불릿도 `쉬운 풀이:` 같은 메타 라벨을 쓰지 마세요.\n"
        "- 허위정보, 필수정보, 표시·광고처럼 뜻이 바로 드러나는 말은 사전식 용어 설명 불릿을 붙이지 마세요. 그런 경우에는 바로 사용자에게 어떤 변화가 생기는지 쉬운 풀이로 넘어가세요.\n"
        "- 원문 요약 문장에 `청문`이 나오면 바로 아래에 반드시 `청문 규정:` 또는 `청문 절차:` 설명 불릿을 붙이세요.\n"
        "- 원문 요약 문장에 `위임·위탁`이 나오면 바로 아래에 반드시 `위임·위탁:` 설명 불릿을 붙이세요.\n"
        "- 원문 요약 문장에 `과태료`가 나오면 바로 아래에 반드시 `과태료:` 설명 불릿을 붙이세요.\n"
        "- 쉬운 풀이 불릿은 사용자에게 말하듯 자연스러운 해요체로 쓰되, `쉽게 말하면,` 같은 고정 접두어를 반복하지 마세요.\n"
        "- 쉬운 풀이 불릿은 고정 접두어 없이 바로 풀어 써도 됩니다. 문장 시작은 항목의 내용에 맞게 자연스럽게 바꾸세요.\n"
        "- 예:\n"
        "  ### 1) 온라인 유통질서 규율 조항군 신설\n\n"
        "  기존 조문 체계에서 제23조는 주로 허가 취소 절차의 청문 규정이었으나, 제안안은 이를 온라인 유통질서 규율 조항군으로 넓힙니다.\n\n"
        "  - 청문 규정: 여기서 `청문`은 처분을 받기 전에 당사자가 설명하고 반론할 수 있는 절차에요.\n"
        "  - 사용자 입장에서는, 문제가 터진 뒤에 벌을 주는 데서 그치지 않고 거래 전에 정보가 맞는지 더 일찍 걸러내겠다는 뜻이에요.\n"
        "## 누구에게 영향이 있나\n"
        "- 영향을 받는 사람과 기관을 5개 안팎으로 나누어 설명하세요.\n"
        "## 봐야 할 점\n"
        "- 시행 전 확인할 쟁점, 집행상 한계, 후속 모니터링 포인트를 4~5개 불릿으로 적으세요.\n"
        "## 확인한 근거\n"
        "- 국회, 법제처, 통계청 등 기관명과 확인한 문서·항목만 짧게 적으세요.\n"
        "- MCP 서버명, 도구명, 함수명, 호출 결과명은 쓰지 마세요.\n\n"
        "작성 규칙:\n"
        "- 내부 조사 과정, MCP 도구 호출 목록, 실패 로그, 리서치 메모를 본문에 쓰지 마세요.\n"
        "- 운영자용 개선 제안 섹션을 만들지 마세요.\n"
        "- 통계청 공식 통계가 관련성이 낮으면 숫자를 억지로 만들지 말고, 필요한 경우 한 문장으로만 한계를 밝히세요.\n"
        "- 짧게 쓴다는 이유로 근거, 영향, 예외를 덜어내지 마세요.\n"
        "- 동어반복, 과장, 번역투를 피하고 짧은 문장을 우선하세요.\n"
        "- 문체는 토스 앱처럼 자연스러운 `-요` 체로 쓰세요.\n"
        "- `합니다`, `됩니다`, `입니다`, `바뀝니다` 같은 `-니다` 체 종결을 쓰지 마세요.\n"
        "- `줄어드어요`처럼 어색한 변환을 쓰지 말고 `줄어들어요`처럼 자연스럽게 쓰세요.\n"
        "- 독자가 바로 봐야 할 **중요 단어**에는 Markdown 볼드체를 적용하세요.\n"
        "- 결론이나 행동 변화처럼 중요한 한 문장에는 `<mark>중요 문장</mark>` 형식으로 하이라이트를 적용하세요.\n"
        "- 볼드체와 하이라이트는 과하게 쓰지 말고, 리포트 전체에서 꼭 필요한 곳에만 쓰세요.\n"
        "- `법제처 API 조회 결과`에 뜻이 있는 법률·행정용어가 본문에 나오면 첫 등장 한 번만 `{{용어:뜻}}` 형식으로 감싸세요.\n"
        "- `{{용어:뜻}}` 안의 뜻은 법제처 API 조회 결과의 정의를 1문장으로 줄여 쓰세요. 이 표기는 화면에서 점선 밑줄과 뜻 툴팁으로 렌더링됩니다.\n"
        "- 법제처 정의가 없는 용어에는 `{{용어:뜻}}` 표기를 쓰지 마세요.\n"
        "- 최종 출력은 Markdown만 작성하세요.\n\n"
        f"{legal_term_context}\n\n"
        f"입력 evidence packet:\n{json.dumps(evidence_payload, ensure_ascii=False, indent=2, default=str)}"
    )


def build_bill_report_batch_prompt(batch_items: list[dict[str, Any]]) -> str:
    return (
        "당신은 Lawdigest의 법안 리포트 작성자입니다.\n"
        "아래 batch_items의 각 항목은 서로 완전히 독립된 작업입니다. "
        "한 법안의 evidence, 표현, 결론, 근거를 다른 법안 리포트에 절대 옮기지 마세요. "
        "각 report_body는 반드시 같은 객체의 bill_id, bill, evidence만 사용해서 작성하세요.\n\n"
        "공통 작성 계약:\n"
        "- 추가 도구 호출, 웹 검색, 셸 명령 실행을 하지 말고 제공된 evidence 안에서만 사실관계를 사용하세요.\n"
        "- 각 항목은 처리 상태와 관계없이 deep_report 긴 버전으로 작성하세요.\n"
        "- 아직 통과되지 않았거나 막 접수된 법안은 제도가 확정된 것처럼 말하지 말고, 법안이 제안하는 변화와 앞으로 볼 점을 중심으로 설명하세요.\n"
        "- 최종 리포트는 6,000~8,000자 안팎이 되도록 근거, 영향, 예외를 충분히 설명하세요.\n"
        "- report_body 안의 Markdown 구조와 문체는 단건 리포트 계약을 따르세요.\n"
        "- report_body에는 `# 법안명`, `## 쉬운 요약`, `## 주요 내용`, `## 왜 나왔나`, "
        "`## 무엇이 달라지나`, `## 누구에게 영향이 있나`, `## 봐야 할 점`, `## 확인한 근거`를 포함하세요.\n"
        "- `## 주요 내용`의 각 불릿은 가능하면 `- **항목 제목**: 쉬운 설명` 형식으로 쓰세요.\n"
        "- `## 무엇이 달라지나` 아래는 반드시 `### 1) 제목`, `### 2) 제목`처럼 번호 헤딩으로 변화 묶음을 나누세요.\n"
        "- 번호 헤딩 다음에는 불릿이 아닌 일반 문단으로 조문 변화 요약을 쓰고, 그 아래에 설명 불릿을 붙이세요.\n"
        "- `## 무엇이 달라지나`를 일반 문단이나 하이라이트 한 문장만으로 끝내지 마세요.\n"
        "- 결론이나 행동 변화처럼 중요한 한 문장에는 `<mark>중요 문장</mark>` 형식으로 하이라이트를 적용하세요.\n"
        "- 문체는 자연스러운 `-요` 체로 쓰고, `합니다`, `됩니다`, `입니다`, `바뀝니다` 같은 `-니다` 체 종결을 쓰지 마세요.\n\n"
        "출력 규칙:\n"
        "- 최종 출력은 JSON 객체 하나만 작성하세요. JSON 앞뒤에 설명, 코드펜스, Markdown을 붙이지 마세요.\n"
        "- reports 배열에는 입력 batch_items와 같은 bill_id를 각각 정확히 한 번씩 넣으세요.\n"
        "- report_body 값은 Markdown 문자열입니다. JSON 문자열 안의 줄바꿈은 반드시 escape된 줄바꿈으로 표현하세요.\n"
        "- brief_summary, gpt_summary, tags를 만들지 마세요. DB 저장용 요약은 별도 코드가 report_body에서 생성합니다.\n\n"
        "출력 스키마:\n"
        '{"reports":[{"bill_id":"PRC_EXAMPLE","report_mode":"deep_report","report_body":"# 예시법안\\n\\n## 쉬운 요약\\n- ..."}]}\n\n'
        f"batch_items:\n{json.dumps(batch_items, ensure_ascii=False, indent=2, default=str)}"
    )


def _extract_json_object(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped).strip()
    if stripped.startswith("{"):
        return stripped
    start = stripped.find("{")
    if start == -1:
        return stripped
    decoder = json.JSONDecoder()
    _, end = decoder.raw_decode(stripped[start:])
    return stripped[start : start + end]


def _parse_batch_report_output(text: str, *, expected_bill_ids: list[str]) -> dict[str, str]:
    try:
        payload = json.loads(_extract_json_object(text))
    except (json.JSONDecodeError, ValueError) as exc:
        raise BillReportGenerationError(
            f"Codex batch report output is not valid JSON: {exc}",
            details={"status": "failed", "expected_bill_ids": expected_bill_ids},
        ) from exc
    reports = payload.get("reports") if isinstance(payload, dict) else None
    if not isinstance(reports, list):
        raise BillReportGenerationError(
            "Codex batch report output must contain a reports array.",
            details={"status": "failed", "expected_bill_ids": expected_bill_ids},
        )
    parsed: dict[str, str] = {}
    for report in reports:
        if not isinstance(report, dict):
            continue
        bill_id = str(report.get("bill_id") or "")
        report_body = report.get("report_body")
        if bill_id and isinstance(report_body, str) and report_body.strip():
            parsed[bill_id] = report_body
    missing = [bill_id for bill_id in expected_bill_ids if bill_id not in parsed]
    if missing:
        raise BillReportGenerationError(
            "Codex batch report output is missing bill reports: " + ", ".join(missing),
            details={"status": "failed", "expected_bill_ids": expected_bill_ids, "missing_bill_ids": missing},
        )
    return parsed


def _markdown_section_body(body: str, heading: str) -> str:
    start = body.find(heading)
    if start == -1:
        return body
    section_start = start + len(heading)
    next_heading = body.find("\n## ", section_start)
    if next_heading == -1:
        return body[section_start:]
    return body[section_start:next_heading]


def _strip_markdown_for_summary(text: str) -> str:
    normalized = text.replace("<mark>", "").replace("</mark>", "")
    normalized = normalized.replace("**", "").replace("`", "")
    normalized = re.sub(r"\{\{([^:{}\n]+):[^{}\n]+\}\}", r"\1", normalized)
    normalized = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", normalized)
    return normalized.strip()


def _has_overlong_brief_prefix(brief_summary: str | None, bill_name: str) -> bool:
    if not brief_summary or not bill_name or not brief_summary.endswith(bill_name):
        return False
    topic = _brief_topic_from_bill_name(bill_name)
    if topic and not brief_summary.startswith(topic):
        return True
    if re.search(r"(된|를|을)(을|를)\s+위한", brief_summary):
        return True
    prefix = brief_summary[: -len(bill_name)].strip()
    prefix = re.sub(r"(을|를)\s+위한$", "", prefix).strip()
    return len(prefix) > 36


def _object_particle(text: str) -> str:
    if not text:
        return "을"
    last = text[-1]
    if "가" <= last <= "힣":
        return "을" if (ord(last) - ord("가")) % 28 else "를"
    return "을"


def _brief_topic_from_bill_name(bill_name: str) -> str | None:
    if not bill_name:
        return None
    if "인공지능 데이터센터" in bill_name:
        return "전력·용수 기반과 인허가 특례로 인공지능 데이터센터 구축·운영 지원"
    if "농지법" in bill_name:
        return "농지 이용 실태조사와 유휴농지 관리 강화"
    if "해운법" in bill_name:
        return "섬 지역 항로 단절 방지와 여객선 운항 지원 강화"
    if "연근해어업" in bill_name:
        return "어업활동 보고와 통합관리시스템 기반 연근해어업 관리체계 구축"
    if "국방반도체" in bill_name:
        return "국방반도체 기술·생산 기반 확충과 안정적 공급망 조성"
    match = re.match(r"(.+?)(?:\s+일부개정법률안|\s+전부개정법률안|\s+제정법률안|\s+법률안|\s+특별법안)", bill_name)
    if not match:
        return None
    subject = match.group(1).strip()
    subject = re.sub(r"^(.+?)에 관한$", r"\1", subject).strip()
    if not subject:
        return None
    return f"{subject} 제도 정비"


def _build_brief_summary_from_report(bill_name: str, report_body: str) -> str | None:
    topic = _brief_topic_from_bill_name(bill_name)
    if topic:
        return f"{topic}{_object_particle(topic)} 위한 {bill_name}"

    easy_summary = _markdown_section_body(report_body, "## 쉬운 요약")
    for line in easy_summary.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        prefix = _strip_markdown_for_summary(stripped[2:])
        prefix = re.sub(r"^(이\s+법안은|법안은)\s*", "", prefix)
        prefix = re.sub(r"(입니다|합니다|이에요|예요|해요|돼요|되요)\.?$", "", prefix).strip()
        prefix = re.sub(r"\s+", " ", prefix)
        prefix = re.sub(r"\s*(특별법|법안)$", "", prefix).strip()
        prefix = re.sub(r"\s*[가-힣A-Za-z0-9·/]+기\s+위한.*$", "", prefix).strip()
        prefix = re.sub(r"\s*(하기|하도록|할 수 있도록)\s+위한.*$", "", prefix).strip()
        prefix = re.sub(r"\s*(위해|위한)$", "", prefix).strip()
        if not prefix:
            continue
        if len(prefix) > 28:
            prefix = prefix[:28].rstrip()
        return f"{prefix}{_object_particle(prefix)} 위한 {bill_name}"
    return None


def _build_db_summary_payload(bill: Dict[str, Any], report_body: str) -> Dict[str, Any]:
    body = report_body.strip()
    body = re.sub(r"^# .+\n+", "", body, count=1)
    evidence_heading = body.find("\n## 확인한 근거")
    if evidence_heading != -1:
        body = body[:evidence_heading].rstrip()

    gpt_summary = body.strip()

    bill_name = str(bill.get("bill_name") or "").strip()
    brief_summary = bill.get("brief_summary")
    if not brief_summary or _has_overlong_brief_prefix(str(brief_summary), bill_name):
        brief_summary = _build_brief_summary_from_report(bill_name, report_body) or brief_summary

    return {
        "brief_summary": brief_summary,
        "gpt_summary": gpt_summary,
        "summary_tags": bill.get("summary_tags"),
    }


def _validate_report_body(report_body: str) -> None:
    body = report_body.strip()
    if not body:
        raise RuntimeError("Codex agent report body is empty.")

    required_headings = ("## 쉬운 요약", "## 주요 내용")
    missing_headings = [heading for heading in required_headings if heading not in body]
    if missing_headings:
        raise RuntimeError("생성 리포트에 필수 섹션이 없습니다: " + ", ".join(missing_headings))

    forbidden_patterns = (
        "Lawdigest 요약 개선 제안",
        "사용한 MCP 도구",
        "MCP 도구",
        "원문 요약:",
        "용어 설명:",
        "법령 체계:",
        "쉬운 풀이:",
        "mcp__",
        "`get_",
        "`search_",
        "`legal_",
        "`query_",
        "내부 조사",
        "리서치 메모",
    )
    leaked_patterns = [pattern for pattern in forbidden_patterns if pattern in body]
    if leaked_patterns:
        raise RuntimeError("생성 리포트에 내부 조사 표현이 남아 있습니다: " + ", ".join(leaked_patterns))

    changes_body = _markdown_section_body(body, "## 무엇이 달라지나")
    explanation_terms = ("청문 규정", "과태료", "위임·위탁")
    missing_explanations = [
        term
        for term in explanation_terms
        if term in changes_body and f"{term}:" not in changes_body and f"**{term}**:" not in changes_body
    ]
    if missing_explanations:
        raise RuntimeError("생성 리포트에 용어 설명 불릿이 없습니다: " + ", ".join(missing_explanations))

    if "청문" in changes_body and all(label not in changes_body for label in ("청문 규정:", "청문 절차:", "청문:")):
        raise RuntimeError("생성 리포트에 청문 용어 설명 불릿이 없습니다.")

    repeated_starters = ("쉽게 말하면,", "쉽게 말해,", "한마디로,")
    repeated = [starter for starter in repeated_starters if changes_body.count(starter) > 1]
    if repeated:
        raise RuntimeError("생성 리포트의 쉬운 풀이 문장 시작이 반복됩니다: " + ", ".join(repeated))

    unnecessary_definition_labels = ("허위정보:", "허위정보 유포:", "필수정보:", "표시·광고:")
    unnecessary_definitions = [label for label in unnecessary_definition_labels if label in changes_body]
    if unnecessary_definitions:
        raise RuntimeError("생성 리포트에 불필요한 용어 설명 불릿이 있습니다: " + ", ".join(unnecessary_definitions))

    easy_starters = repeated_starters + ("사용자 입장에서는,", "바뀌는 점은,", "실제로는,", "이 말은", "결국")
    unbulleted_easy_starters = [
        starter
        for starter in easy_starters
        if re.search(rf"(?m)^(?!\s*-\s)\s*{re.escape(starter)}", changes_body)
    ]
    if unbulleted_easy_starters:
        raise RuntimeError(
            "생성 리포트의 쉬운 풀이 문장은 Markdown 불릿이어야 합니다: "
            + ", ".join(unbulleted_easy_starters)
        )

    term_labels = ("청문 규정:", "청문 절차:", "청문:", "과태료:", "위임·위탁:")
    unbulleted_labels = [
        label
        for label in term_labels
        if label in changes_body and f"\n- {label}" not in changes_body and f"\n  - {label}" not in changes_body
    ]
    if unbulleted_labels:
        raise RuntimeError("생성 리포트의 용어 설명 문장은 Markdown 불릿이어야 합니다: " + ", ".join(unbulleted_labels))

    if changes_body.strip() and not re.search(r"(?m)^### 1\)\s+\S", changes_body):
        raise RuntimeError("생성 리포트의 변화 설명은 번호 헤딩 형식이어야 합니다.")

    sentence_style_headings = [
        heading
        for heading in re.findall(r"(?m)^###\s+\d+\)\s+(.+)$", changes_body)
        if re.search(r"(한다|둔다|넓힌다|바꾼다|늘린다|줄인다)$", heading.strip())
    ]
    if sentence_style_headings:
        raise RuntimeError("생성 리포트의 변화 제목은 짧은 명사형 제목이어야 합니다: " + ", ".join(sentence_style_headings))

    hard_heading_terms = ("집행주체", "체계 개정", "확충", "정교화")
    hard_change_headings = [
        heading
        for heading in re.findall(r"(?m)^###\s+\d+\)\s+(.+)$", changes_body)
        if any(term in heading for term in hard_heading_terms)
    ]
    if hard_change_headings:
        raise RuntimeError("생성 리포트의 변화 제목은 쉬운 변화 제목이어야 합니다: " + ", ".join(hard_change_headings))

    major_body = _markdown_section_body(body, "## 주요 내용")
    unbolded_major_labels = [
        line.strip()
        for line in major_body.splitlines()
        if line.startswith("- ") and ": " in line and not re.match(r"- \*\*[^*\n]+\*\*:", line)
    ]
    if unbolded_major_labels:
        raise RuntimeError("생성 리포트의 콜론 앞 핵심 라벨은 볼드체여야 합니다: " + ", ".join(unbolded_major_labels))

    if not re.search(r"\*\*[^*\n][^*\n]*\*\*", body):
        raise RuntimeError("생성 리포트에 중요 단어 볼드체가 없습니다.")

    if not re.search(r"<mark>[^<>\n]+</mark>", body):
        raise RuntimeError("생성 리포트에 중요 문장 하이라이트가 없습니다.")

    body_without_term_tooltips = re.sub(r"\{\{([^:{}\n]+):[^{}\n]+\}\}", r"\1", body)
    remaining_formal_endings = sorted(set(re.findall(r"[가-힣]+니다\.", body_without_term_tooltips)))
    if remaining_formal_endings:
        raise RuntimeError("생성 리포트에 토스식 -요 체가 아닌 격식체 종결이 남아 있습니다: " + ", ".join(remaining_formal_endings))

    awkward_yo_tone = ("줄어드어요",)
    awkward_matches = [phrase for phrase in awkward_yo_tone if phrase in body]
    if awkward_matches:
        raise RuntimeError("생성 리포트에 어색한 -요 체가 남아 있습니다: " + ", ".join(awkward_matches))


def _repair_report_body(report_body: str) -> str:
    repaired = report_body.replace("원문 요약:", "").replace("용어 설명:", "")
    repaired = repaired.replace("법령 체계:", "").replace("쉬운 풀이:", "")

    term_labels = ("청문 규정:", "청문 절차:", "청문:", "과태료:", "위임·위탁:")
    easy_starters = (
        "쉽게 말하면,",
        "쉽게 말해,",
        "한마디로,",
        "사용자 입장에서는,",
        "바뀌는 점은,",
        "실제로는,",
        "이 말은",
        "결국",
    )
    fixed_lines: list[str] = []
    in_changes = False
    for line in repaired.splitlines():
        stripped = line.strip()
        if stripped == "## 무엇이 달라지나":
            in_changes = True
        elif stripped.startswith("## ") and stripped != "## 무엇이 달라지나":
            in_changes = False

        if in_changes and stripped:
            already_bulleted = stripped.startswith("- ")
            if not already_bulleted and any(stripped.startswith(label) for label in term_labels + easy_starters):
                indent = line[: len(line) - len(line.lstrip())]
                fixed_lines.append(f"{indent}- {stripped}")
                continue

        if stripped.startswith("- ") and ": " in stripped and not re.match(r"- \*\*[^*\n]+\*\*:", stripped):
            label, rest = stripped[2:].split(": ", 1)
            if 1 <= len(label) <= 24 and not label.startswith("http"):
                indent = line[: len(line) - len(line.lstrip())]
                fixed_lines.append(f"{indent}- **{label}**: {rest}")
                continue

        fixed_lines.append(line)

    repaired = "\n".join(fixed_lines).strip()
    if "<mark>" not in repaired:
        for pattern in (
            r"(?m)^(-\s+[^.\n!?]*\*\*[^*\n]+\*\*[^.\n!?]*[.!?]?요\.)",
            r"(?m)^([^-\n#][^.\n!?]*\*\*[^*\n]+\*\*[^.\n!?]*[.!?]?요\.)",
        ):
            match = re.search(pattern, repaired)
            if match:
                sentence = match.group(1)
                repaired = repaired[: match.start(1)] + f"<mark>{sentence}</mark>" + repaired[match.end(1) :]
                break

    if not re.search(r"\*\*[^*\n][^*\n]*\*\*", repaired):
        repaired = re.sub(
            r"(?m)^- ([^.\n]{2,24}?)(이라는|라는|을|를|에 대한|에 관한|이 |가 )",
            r"- **\1**\2",
            repaired,
            count=1,
        )

    return repaired + "\n"


def _fetch_bill_report_targets(
    mode: str,
    limit: int,
    read_mode: str | None = None,
    target: str = "passed",
) -> List[Dict[str, Any]]:
    if limit < 1:
        raise ValueError("limit는 1 이상이어야 합니다.")
    if target not in TARGETS:
        raise ValueError("target은 passed, pending, all 중 하나여야 합니다.")

    db_mode = _resolve_read_mode(mode, read_mode)
    bill_columns = get_bill_table_columns(mode=db_mode)
    filters = ["summary IS NOT NULL", "summary != ''"]
    params: list[Any] = []
    if target in {"passed", "pending"}:
        result_filters = " OR ".join(["COALESCE(bill_result, '') LIKE %s" for _ in PASSED_RESULT_TERMS])
        stage_filters = " OR ".join(["COALESCE(stage, '') LIKE %s" for _ in PASSED_STAGE_TERMS])
        passed_clause = f"({result_filters} OR {stage_filters})"
        excluded_filters = " AND ".join(["COALESCE(bill_result, '') NOT LIKE %s" for _ in EXCLUDED_RESULT_TERMS])
        filters.append(passed_clause if target == "passed" else f"NOT {passed_clause}")
        filters.append(excluded_filters)
        params.extend([f"%{term}%" for term in PASSED_RESULT_TERMS])
        params.extend([f"%{term}%" for term in PASSED_STAGE_TERMS])
        params.extend([f"%{term}%" for term in EXCLUDED_RESULT_TERMS])
    where_clause = "\n        AND ".join(filters)
    summary_tags_select = "summary_tags" if "summary_tags" in bill_columns else "NULL AS summary_tags"
    query = f"""
    SELECT
        bill_id,
        bill_number,
        bill_name,
        summary,
        brief_summary,
        {summary_tags_select},
        proposers,
        proposer_kind,
        propose_date,
        stage,
        committee,
        bill_result,
        bill_link,
        bill_pdf_url
    FROM Bill
    WHERE
        {where_clause}
    ORDER BY propose_date DESC, bill_id DESC
    LIMIT %s
    """
    params.append(limit)

    conn = get_db_connection(mode=db_mode)
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return list(cur.fetchall())
    finally:
        conn.close()


def _fetch_passed_bills(mode: str, limit: int, read_mode: str | None = None) -> List[Dict[str, Any]]:
    return _fetch_bill_report_targets(mode=mode, limit=limit, read_mode=read_mode, target="passed")


@dataclass(frozen=True)
class CodexBillReportAgent:
    cli_bin: str = DEFAULT_CODEX_BIN
    model: str = DEFAULT_CODEX_MODEL
    timeout_seconds: int = DEFAULT_CODEX_TIMEOUT_SECONDS
    workdir: str = DEFAULT_AGENT_WORKDIR
    codex_home: str = DEFAULT_CODEX_HOME
    enable_mcp: bool = False

    def build_environment(self) -> dict[str, str]:
        env = os.environ.copy()
        codex_home = Path(self.codex_home).expanduser()
        codex_home.mkdir(parents=True, exist_ok=True)

        source_home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex").expanduser()
        if source_home.resolve() != codex_home.resolve():
            for filename in CODEX_AUTH_FILES:
                source = source_home / filename
                target = codex_home / filename
                if not source.exists() or target.exists() or target.is_symlink():
                    continue
                target.symlink_to(source)

        _write_report_codex_config(codex_home=codex_home, workdir=self.workdir)
        env["CODEX_HOME"] = str(codex_home)
        return env

    def _mcp_server_config_args(self) -> list[str]:
        assembly_key = os.getenv("ASSEMBLY_API_KEY") or os.getenv("APIKEY_billsInfo") or os.getenv("APIKEY_status")
        if not assembly_key:
            raise RuntimeError("ASSEMBLY_API_KEY 환경변수가 필요합니다.")
        law_oc = os.getenv("LAW_OC", "")
        kosis_key = os.getenv("KOSIS_API_KEY", "")
        config: dict[str, dict[str, Any]] = {
            "korean-stats": {
                "command": "npx",
                "args": ["-y", "mcp-remote", "https://korean-stats-mcp.fly.dev/mcp"],
                "env": {"KOSIS_API_KEY": kosis_key} if kosis_key else {},
            },
            "korean-law": {
                "command": "npx",
                "args": ["-y", "korean-law-mcp@latest"],
                "env": {"LAW_OC": law_oc} if law_oc else {},
            },
            "assembly-api": {
                "command": "npx",
                "args": ["-y", "assembly-api-mcp@latest"],
                "env": {
                    "ASSEMBLY_API_KEY": assembly_key,
                    "MCP_PROFILE": "full",
                    "MCP_TRANSPORT": "stdio",
                },
            },
            "open-assembly": {
                "command": "uvx",
                "args": ["open-assembly-mcp@latest"],
                "env": {"ASSEMBLY_API_KEY": assembly_key},
            },
        }

        args: list[str] = []
        for server_name, server in config.items():
            prefix = f"mcp_servers.{server_name}"
            args.extend(["-c", f"{prefix}.command={_toml_string(server['command'])}"])
            args.extend(["-c", f"{prefix}.args={_toml_array(server['args'])}"])
            if server.get("env"):
                args.extend(["-c", f"{prefix}.env={_toml_inline_table(server['env'])}"])
            for tool_name in MCP_APPROVED_TOOLS.get(server_name, ()):
                args.extend(["-c", f"{prefix}.tools.{tool_name}.approval_mode={_toml_string('approve')}"])
        return args

    def build_command(self, *, prompt: str, output_path: str) -> tuple[list[str], str]:
        command = [
            self.cli_bin,
            "exec",
            "--disable",
            "plugins",
            "--disable",
            "apps",
            "--disable",
            "memories",
            "--sandbox",
            "read-only",
            "--cd",
            self.workdir,
            "--skip-git-repo-check",
            "--ephemeral",
            "--ignore-rules",
            "--json",
            "--model",
            self.model,
            "--output-last-message",
            output_path,
            "-",
        ]
        if self.enable_mcp:
            command[-1:-1] = self._mcp_server_config_args()
        return command, prompt

    def write_report(
        self,
        *,
        bill: Dict[str, Any],
        output_path: str,
        inspection_dir: str | None = None,
        report_mode: str = "auto",
    ) -> Dict[str, Any]:
        evidence = build_bill_report_evidence(bill, report_mode=report_mode)
        resolved_mode = str(evidence.get("report_mode") or _resolve_report_mode(report_mode, bill))
        prompt = build_bill_report_prompt(bill, report_mode=resolved_mode, evidence=evidence)
        command, stdin_text = self.build_command(prompt=prompt, output_path=output_path)
        report_path = Path(output_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        started_at = datetime.now(timezone.utc)
        started_perf = time.perf_counter()

        try:
            proc = subprocess.run(
                command,
                input=stdin_text,
                capture_output=True,
                text=True,
                cwd=self.workdir,
                env=self.build_environment(),
                timeout=self.timeout_seconds,
            )
            stdout_text = (proc.stdout or "").strip()
            stderr_text = (proc.stderr or "").strip()
            exit_code = proc.returncode
        except Exception:
            raise
        finally:
            finished_at = datetime.now(timezone.utc)
            duration_seconds = round(time.perf_counter() - started_perf, 3)

        metadata = _parse_codex_json_metadata(stdout_text)
        details = {
            "bill_id": bill.get("bill_id"),
            "bill_name": bill.get("bill_name"),
            "report_path": str(report_path),
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "duration_seconds": duration_seconds,
            "exit_code": exit_code,
            **metadata,
        }
        validation = {"status": "not_run", "summary": "리포트 생성 실패로 Markdown 검증을 실행하지 않았습니다."}
        if exit_code != 0:
            if inspection_dir:
                inspection_paths = _write_inspection_artifacts(
                    inspection_dir=Path(inspection_dir),
                    bill=bill,
                    prompt=prompt,
                    command=command,
                    stdout_text=stdout_text,
                    stderr_text=stderr_text,
                    report_path=report_path,
                    details=details,
                    validation=validation,
                )
                details.update(inspection_paths)
            error = (stderr_text or stdout_text or "Codex agent failed").strip()
            raise BillReportGenerationError(error, details=details)
        if not report_path.exists() and stdout_text:
            report_path.write_text(stdout_text, encoding="utf-8")
        if not report_path.exists():
            if inspection_dir:
                inspection_paths = _write_inspection_artifacts(
                    inspection_dir=Path(inspection_dir),
                    bill=bill,
                    prompt=prompt,
                    command=command,
                    stdout_text=stdout_text,
                    stderr_text=stderr_text,
                    report_path=report_path,
                    details=details,
                    validation=validation,
                )
                details.update(inspection_paths)
            raise BillReportGenerationError("Codex agent report body is empty.", details=details)
        raw_report_body = report_path.read_text(encoding="utf-8")
        repaired_report_body = _repair_report_body(raw_report_body)
        repair_applied = repaired_report_body != raw_report_body.strip() + "\n"
        if repair_applied:
            report_path.write_text(repaired_report_body, encoding="utf-8")
        output_bytes = report_path.stat().st_size
        details["output_bytes"] = output_bytes
        details["report_mode"] = resolved_mode
        details["prefetch"] = {
            "plan": EFFECTIVE_AGENT_TOOL_AUDIT["effective_prefetch"],
            "errors": evidence.get("prefetch_errors") or [],
        }
        details["repair_applied"] = repair_applied
        try:
            _validate_report_body(report_path.read_text(encoding="utf-8"))
            validation_summary = "Markdown 리포트 품질 검증을 통과했습니다."
            if repair_applied:
                validation_summary = "Markdown 리포트 형식 cheap repair 후 품질 검증을 통과했습니다."
            validation = {"status": "passed", "summary": validation_summary}
        except RuntimeError as exc:
            validation = {"status": "failed", "summary": str(exc)}
            if inspection_dir:
                inspection_paths = _write_inspection_artifacts(
                    inspection_dir=Path(inspection_dir),
                    bill=bill,
                    prompt=prompt,
                    command=command,
                    stdout_text=stdout_text,
                    stderr_text=stderr_text,
                    report_path=report_path,
                    details=details,
                    validation=validation,
                )
                details.update(inspection_paths)
            raise BillReportGenerationError(str(exc), details=details) from exc

        if inspection_dir:
            inspection_paths = _write_inspection_artifacts(
                inspection_dir=Path(inspection_dir),
                bill=bill,
                prompt=prompt,
                command=command,
                stdout_text=stdout_text,
                stderr_text=stderr_text,
                report_path=report_path,
                details=details,
                validation=validation,
            )
            details.update(inspection_paths)

        return {
            **details,
            "status": "success",
        }

    def write_reports_batch(
        self,
        *,
        bills: list[dict[str, Any]],
        output_root: Path,
        inspection_dir: str | None = None,
        report_mode: str = "auto",
        batch_index: int = 1,
    ) -> dict[str, Any]:
        batch_items: list[dict[str, Any]] = []
        evidences: dict[str, dict[str, Any]] = {}
        for bill in bills:
            bill_id = str(bill.get("bill_id") or "")
            evidence = build_bill_report_evidence(bill, report_mode=report_mode)
            resolved_mode = str(evidence.get("report_mode") or _resolve_report_mode(report_mode, bill))
            evidences[bill_id] = evidence
            batch_items.append({
                "bill_id": bill_id,
                "bill": _build_bill_payload(bill),
                "report_mode": resolved_mode,
                "evidence": evidence,
            })

        expected_bill_ids = [str(bill.get("bill_id") or "") for bill in bills]
        prompt = build_bill_report_batch_prompt(batch_items)
        batch_output_path = output_root / f"batch-session-{batch_index:04d}.json"
        command, stdin_text = self.build_command(prompt=prompt, output_path=str(batch_output_path))
        batch_output_path.parent.mkdir(parents=True, exist_ok=True)
        started_at = datetime.now(timezone.utc)
        started_perf = time.perf_counter()

        try:
            proc = subprocess.run(
                command,
                input=stdin_text,
                capture_output=True,
                text=True,
                cwd=self.workdir,
                env=self.build_environment(),
                timeout=self.timeout_seconds,
            )
            stdout_text = (proc.stdout or "").strip()
            stderr_text = (proc.stderr or "").strip()
            exit_code = proc.returncode
        finally:
            finished_at = datetime.now(timezone.utc)
            duration_seconds = round(time.perf_counter() - started_perf, 3)

        metadata = _parse_codex_json_metadata(stdout_text)
        session = {
            "batch_index": batch_index,
            "bill_ids": expected_bill_ids,
            "output_path": str(batch_output_path),
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "duration_seconds": duration_seconds,
            "exit_code": exit_code,
            **metadata,
        }
        if exit_code != 0:
            error = (stderr_text or stdout_text or "Codex agent failed").strip()
            failed_items = [
                {
                    "bill_id": bill.get("bill_id"),
                    "bill_name": bill.get("bill_name"),
                    "status": "failed",
                    "error": error,
                    "batch_index": batch_index,
                    "started_at": started_at.isoformat(),
                    "finished_at": finished_at.isoformat(),
                    "duration_seconds": duration_seconds,
                    "exit_code": exit_code,
                    "codex_thread_id": metadata.get("codex_thread_id"),
                    "codex_event_count": metadata.get("codex_event_count"),
                    "token_usage_available": False,
                }
                for bill in bills
            ]
            return {"items": failed_items, "session": session}

        output_text = ""
        if batch_output_path.exists():
            output_text = batch_output_path.read_text(encoding="utf-8")
        if not output_text.strip():
            output_text = stdout_text

        try:
            reports_by_bill_id = _parse_batch_report_output(output_text, expected_bill_ids=expected_bill_ids)
        except BillReportGenerationError as exc:
            failed_items = [
                {
                    "bill_id": bill.get("bill_id"),
                    "bill_name": bill.get("bill_name"),
                    "status": "failed",
                    "error": str(exc),
                    "batch_index": batch_index,
                    "started_at": started_at.isoformat(),
                    "finished_at": finished_at.isoformat(),
                    "duration_seconds": duration_seconds,
                    "exit_code": exit_code,
                    "codex_thread_id": metadata.get("codex_thread_id"),
                    "codex_event_count": metadata.get("codex_event_count"),
                    "token_usage_available": False,
                }
                for bill in bills
            ]
            return {"items": failed_items, "session": session}

        completed_items: list[dict[str, Any]] = []
        for bill in bills:
            bill_id = str(bill.get("bill_id") or "")
            report_path = output_root / f"{_slugify_bill_id(bill_id)}.md"
            details = {
                "bill_id": bill.get("bill_id"),
                "bill_name": bill.get("bill_name"),
                "report_path": str(report_path),
                "started_at": started_at.isoformat(),
                "finished_at": finished_at.isoformat(),
                "duration_seconds": duration_seconds,
                "exit_code": exit_code,
                "batch_index": batch_index,
                "codex_thread_id": metadata.get("codex_thread_id"),
                "codex_event_count": metadata.get("codex_event_count"),
                "token_usage_available": False,
                "usage_shared": True,
                "report_mode": str(evidences.get(bill_id, {}).get("report_mode") or _resolve_report_mode(report_mode, bill)),
                "prefetch": {
                    "plan": EFFECTIVE_AGENT_TOOL_AUDIT["effective_prefetch"],
                    "errors": evidences.get(bill_id, {}).get("prefetch_errors") or [],
                },
            }
            validation = {"status": "not_run", "summary": "Markdown 검증을 실행하지 않았습니다."}
            try:
                raw_report_body = reports_by_bill_id[bill_id]
                repaired_report_body = _repair_report_body(raw_report_body)
                repair_applied = repaired_report_body != raw_report_body.strip() + "\n"
                report_path.write_text(repaired_report_body, encoding="utf-8")
                details["output_bytes"] = report_path.stat().st_size
                details["repair_applied"] = repair_applied
                _validate_report_body(report_path.read_text(encoding="utf-8"))
                validation_summary = "Markdown 리포트 품질 검증을 통과했습니다."
                if repair_applied:
                    validation_summary = "Markdown 리포트 형식 cheap repair 후 품질 검증을 통과했습니다."
                validation = {"status": "passed", "summary": validation_summary}
                status_item = {**details, "status": "success"}
            except Exception as exc:
                validation = {"status": "failed", "summary": str(exc)}
                status_item = {**details, "status": "failed", "error": str(exc)}

            if inspection_dir:
                inspection_paths = _write_inspection_artifacts(
                    inspection_dir=Path(inspection_dir),
                    bill=bill,
                    prompt=prompt,
                    command=command,
                    stdout_text=stdout_text,
                    stderr_text=stderr_text,
                    report_path=report_path,
                    details=details,
                    validation=validation,
                )
                status_item.update(inspection_paths)
            completed_items.append(status_item)

        return {"items": completed_items, "session": session}


def run_agentic_bill_reports(
    *,
    mode: str = "dry_run",
    limit: int = 5,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    read_mode: str | None = None,
    codex_model: str | None = None,
    stop_on_error: bool = False,
    target: str = "passed",
    usage_meter: dict[str, Any] | None = None,
    concurrency: int = 1,
    inspection: bool = False,
    report_mode: str = "auto",
    batch_session_size: int = DEFAULT_BATCH_SESSION_SIZE,
) -> Dict[str, Any]:
    if limit < 1:
        raise ValueError("limit는 1 이상이어야 합니다.")
    if target not in TARGETS:
        raise ValueError("target은 passed, pending, all 중 하나여야 합니다.")
    if concurrency < 1:
        raise ValueError("concurrency는 1 이상이어야 합니다.")
    if report_mode not in REPORT_MODES:
        raise ValueError("report_mode은 auto, summary, deep_report 중 하나여야 합니다.")
    if batch_session_size < 1:
        raise ValueError("batch_session_size는 1 이상이어야 합니다.")
    if batch_session_size > MAX_BATCH_SESSION_SIZE:
        raise ValueError(f"batch_session_size는 {MAX_BATCH_SESSION_SIZE} 이하여야 합니다.")

    targets = _fetch_bill_report_targets(mode=mode, limit=limit, read_mode=read_mode, target=target)
    output_root = Path(output_dir).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    inspection_dir = output_root / "inspection" if inspection else None
    if inspection_dir is not None:
        inspection_dir.mkdir(parents=True, exist_ok=True)
    agent = CodexBillReportAgent(model=codex_model or DEFAULT_CODEX_MODEL)
    items: list[dict[str, Any] | None] = [None] * len(targets)
    sessions: list[dict[str, Any]] = []
    started_at = datetime.now(timezone.utc)
    started_perf = time.perf_counter()

    def generate_one(index: int, bill: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        bill_id = bill.get("bill_id")
        report_path = output_root / f"{_slugify_bill_id(bill_id)}.md"
        try:
            return index, agent.write_report(
                bill=bill,
                output_path=str(report_path),
                inspection_dir=str(inspection_dir) if inspection_dir is not None else None,
                report_mode=report_mode,
            )
        except BillReportGenerationError as exc:
            failed = {
                **exc.details,
                "status": "failed",
                "error": str(exc),
            }
            if stop_on_error:
                raise
            return index, failed
        except Exception as exc:
            failed = {
                "bill_id": bill_id,
                "bill_name": bill.get("bill_name"),
                "report_path": str(report_path),
                "status": "failed",
                "error": str(exc),
            }
            if stop_on_error:
                raise
            return index, failed

    def generate_batch(start_index: int, bills: list[dict[str, Any]], batch_index: int) -> None:
        try:
            batch_result = agent.write_reports_batch(
                bills=bills,
                output_root=output_root,
                inspection_dir=str(inspection_dir) if inspection_dir is not None else None,
                report_mode=report_mode,
                batch_index=batch_index,
            )
        except Exception as exc:
            if stop_on_error:
                raise
            batch_result = {
                "items": [
                    {
                        "bill_id": bill.get("bill_id"),
                        "bill_name": bill.get("bill_name"),
                        "report_path": str(output_root / f"{_slugify_bill_id(bill.get('bill_id'))}.md"),
                        "status": "failed",
                        "error": str(exc),
                        "batch_index": batch_index,
                    }
                    for bill in bills
                ],
                "session": {
                    "batch_index": batch_index,
                    "bill_ids": [str(bill.get("bill_id") or "") for bill in bills],
                    "token_usage_available": False,
                },
            }
        sessions.append(batch_result["session"])
        for offset, item in enumerate(batch_result["items"]):
            items[start_index + offset] = item
        if stop_on_error and any(item.get("status") == "failed" for item in batch_result["items"]):
            first_failed = next(item for item in batch_result["items"] if item.get("status") == "failed")
            raise BillReportGenerationError(str(first_failed.get("error") or "batch failed"), details=first_failed)

    if targets and batch_session_size > 1 and len(targets) > 1:
        for batch_index, start_index in enumerate(range(0, len(targets), batch_session_size), start=1):
            generate_batch(start_index, targets[start_index : start_index + batch_session_size], batch_index)
    elif targets and concurrency > 1:
        with ThreadPoolExecutor(max_workers=min(concurrency, len(targets))) as executor:
            futures = [executor.submit(generate_one, index, bill) for index, bill in enumerate(targets)]
            for future in as_completed(futures):
                index, item = future.result()
                items[index] = item
    else:
        for index, bill in enumerate(targets):
            item_index, item = generate_one(index, bill)
            items[item_index] = item

    completed_items = [item for item in items if item is not None]
    finished_at = datetime.now(timezone.utc)
    total_duration_seconds = round(time.perf_counter() - started_perf, 3)
    usage_totals: dict[str, int] = {}
    for item in completed_items:
        usage = item.get("usage")
        if not isinstance(usage, dict):
            continue
        for key, value in usage.items():
            if isinstance(value, int):
                usage_totals[key] = usage_totals.get(key, 0) + value
    for session in sessions:
        usage = session.get("usage")
        if not isinstance(usage, dict):
            continue
        for key, value in usage.items():
            if isinstance(value, int):
                usage_totals[key] = usage_totals.get(key, 0) + value

    db_upserted_count = 0
    if mode != "dry_run":
        for item in completed_items:
            if item.get("status") != "success":
                continue
            bill = next((target_bill for target_bill in targets if target_bill.get("bill_id") == item.get("bill_id")), None)
            if not bill:
                continue
            report_path = item.get("report_path")
            if not report_path:
                continue
            payload = _build_db_summary_payload(
                bill=bill,
                report_body=Path(str(report_path)).read_text(encoding="utf-8"),
            )
            update_bill_summary(
                bill_id=str(item["bill_id"]),
                brief_summary=payload.get("brief_summary"),
                gpt_summary=payload.get("gpt_summary"),
                summary_tags=payload.get("summary_tags"),
                mode=_db_mode_for_execution(mode),
                category=payload.get("category"),
            )
            db_upserted_count += 1

    report = {
        "execution_mode": mode,
        "read_mode": _resolve_read_mode(mode, read_mode),
        "provider": "codex-agent",
        "model": codex_model or DEFAULT_CODEX_MODEL,
        "target": {"all": "all_bills", "pending": "pending_bills"}.get(target, "passed_bills"),
        "report_mode": report_mode,
        "concurrency": concurrency,
        "batch_session_size": batch_session_size,
        "batch_session_count": len(sessions) if batch_session_size > 1 else len(completed_items),
        "inspection": {
            "enabled": inspection,
            "output_dir": str(inspection_dir) if inspection_dir is not None else None,
        },
        "output_dir": str(output_root),
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "processed_at": finished_at.isoformat(),
        "stats": {
            "target_count": len(targets),
            "processed_count": len(completed_items),
            "success_count": sum(1 for item in completed_items if item["status"] == "success"),
            "failure_count": sum(1 for item in completed_items if item["status"] == "failed"),
            "total_duration_seconds": total_duration_seconds,
            "token_usage_available_count": (
                sum(1 for item in completed_items if item.get("token_usage_available"))
                + sum(1 for session in sessions if session.get("token_usage_available"))
            ),
            "usage_totals": usage_totals,
            "db_upserted_count": db_upserted_count,
        },
        "items": completed_items,
        "sessions": sessions,
    }
    normalized_usage_meter = _normalize_usage_meter(usage_meter)
    if normalized_usage_meter is not None:
        report["usage_meter"] = normalized_usage_meter
    (output_root / "manifest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return report
