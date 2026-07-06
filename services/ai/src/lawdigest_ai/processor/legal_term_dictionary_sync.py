from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from lawdigest_ai.db import get_db_connection
from lawdigest_ai.processor.law_open_api_terms import LawOpenApiTermClient


def normalize_legal_term(term: str) -> str:
    return re.sub(r"\s+", "", term.replace("ㆍ", "·")).strip()


def _first_text(*values: Any) -> str | None:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return None


def _row_term(row: dict[str, Any]) -> str | None:
    return _first_text(row.get("법령용어명"), row.get("term"), row.get("용어명"))


def _row_term_id(row: dict[str, Any]) -> str | None:
    return _first_text(row.get("법령용어ID"), row.get("trmSeqs"), row.get("ID"))


def _build_dictionary_item(client: LawOpenApiTermClient, row: dict[str, Any]) -> dict[str, Any] | None:
    term = _row_term(row)
    if not term:
        return None
    definitions, sources = client.get_legal_term_definitions(term)
    if not definitions:
        return None
    return {
        "source": "law.go.kr",
        "source_term_id": _row_term_id(row),
        "term": term,
        "normalized_term": normalize_legal_term(term),
        "definition": definitions[0],
        "definition_sources": json.dumps(list(sources), ensure_ascii=False),
        "raw_payload": json.dumps(row, ensure_ascii=False, default=str),
    }


def _upsert_dictionary_items(items: list[dict[str, Any]], *, mode: str) -> int:
    if not items:
        return 0

    synced_at = datetime.now(timezone.utc).replace(tzinfo=None)
    conn = get_db_connection(mode=mode)
    try:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO LegalTermDictionary (
                    source,
                    source_term_id,
                    term,
                    normalized_term,
                    definition,
                    definition_sources,
                    raw_payload,
                    enabled,
                    last_synced_at
                ) VALUES (
                    %(source)s,
                    %(source_term_id)s,
                    %(term)s,
                    %(normalized_term)s,
                    %(definition)s,
                    CAST(%(definition_sources)s AS JSON),
                    CAST(%(raw_payload)s AS JSON),
                    TRUE,
                    %(last_synced_at)s
                )
                ON DUPLICATE KEY UPDATE
                    source_term_id = VALUES(source_term_id),
                    term = VALUES(term),
                    definition = VALUES(definition),
                    definition_sources = VALUES(definition_sources),
                    raw_payload = VALUES(raw_payload),
                    enabled = TRUE,
                    last_synced_at = VALUES(last_synced_at)
                """,
                [{**item, "last_synced_at": synced_at} for item in items],
            )
        conn.commit()
        return len(items)
    finally:
        conn.close()


def fetch_legal_term_dictionary_items(
    *,
    query: str,
    page_size: int = 100,
    max_pages: int = 1,
    limit: int | None = None,
    client: LawOpenApiTermClient | None = None,
) -> list[dict[str, Any]]:
    if page_size < 1:
        raise ValueError("page_size는 1 이상이어야 합니다.")
    if max_pages < 1:
        raise ValueError("max_pages는 1 이상이어야 합니다.")
    if limit is not None and limit < 1:
        raise ValueError("limit는 1 이상이어야 합니다.")

    term_client = client or LawOpenApiTermClient()
    if not term_client.enabled:
        raise RuntimeError("LAW_OC 환경변수가 필요합니다.")

    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for page in range(1, max_pages + 1):
        rows = term_client.search_legal_dictionary_terms(query, display=page_size, page=page)
        if not rows:
            break
        for row in rows:
            item = _build_dictionary_item(term_client, row)
            if not item or item["normalized_term"] in seen:
                continue
            seen.add(item["normalized_term"])
            items.append(item)
            if limit is not None and len(items) >= limit:
                return items
        if len(rows) < page_size:
            break
    return items


def run_legal_term_dictionary_sync(
    *,
    mode: str = "dry_run",
    query: str = "가",
    page_size: int = 100,
    max_pages: int = 1,
    limit: int | None = None,
    client: LawOpenApiTermClient | None = None,
) -> dict[str, Any]:
    if mode not in {"dry_run", "test", "prod"}:
        raise ValueError("mode는 dry_run, test, prod 중 하나여야 합니다.")

    items = fetch_legal_term_dictionary_items(
        query=query,
        page_size=page_size,
        max_pages=max_pages,
        limit=limit,
        client=client,
    )
    upserted = 0 if mode == "dry_run" else _upsert_dictionary_items(items, mode=mode)
    return {
        "mode": mode,
        "query": query,
        "page_size": page_size,
        "max_pages": max_pages,
        "limit": limit,
        "fetched_count": len(items),
        "upserted_count": upserted,
        "dry_run": mode == "dry_run",
        "terms": [item["term"] for item in items[:20]],
    }
