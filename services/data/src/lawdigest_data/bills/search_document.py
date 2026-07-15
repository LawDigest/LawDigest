from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional


def _coerce_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return " ".join(text.split())


def build_bill_search_document(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    bill_id = _coerce_text(row.get("bill_id"))
    if not bill_id:
        return None

    bill_name = _coerce_text(row.get("bill_name"))
    title = _coerce_text(row.get("title"))
    gpt_summary = _coerce_text(row.get("gpt_summary"))
    raw_summary = _coerce_text(row.get("summary"))
    search_parts = [
        bill_name,
        bill_name,
        bill_name,
        title,
        title,
        gpt_summary,
        raw_summary,
    ]

    return {
        "bill_id": bill_id,
        "bill_name_text": bill_name,
        "title_text": title,
        "gpt_summary_text": gpt_summary,
        "raw_summary_text": raw_summary,
        "search_text": "\n".join(part for part in search_parts if part),
        "source_modified_date": row.get("source_modified_date") or row.get("modified_date"),
    }


def build_bill_search_documents(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    documents: List[Dict[str, Any]] = []
    for row in rows:
        document = build_bill_search_document(row)
        if document is not None:
            documents.append(document)
    return documents
