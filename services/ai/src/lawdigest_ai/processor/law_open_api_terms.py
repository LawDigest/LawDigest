from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests


LAW_OPEN_API_BASE_URL = "https://www.law.go.kr/DRF"


class LawOpenApiTermClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class LawOpenApiTerm:
    term: str
    source: str
    definitions: tuple[str, ...] = ()
    definition_sources: tuple[str, ...] = ()
    related_daily_terms: tuple[str, ...] = ()
    related_legal_terms: tuple[str, ...] = ()


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _compact_unique(values: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    compacted: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        compacted.append(normalized)
    return tuple(compacted)


def _definition_score(definition: str) -> tuple[int, int]:
    narrow_markers = ("법 제", "규정에 따른", "장관", "기관장", "검사기관", "고시", "훈령")
    general_markers = ("절차를 말한다", "것을 말한다", "의견을 직접 듣고", "증거를 조사")
    narrow_score = sum(1 for marker in narrow_markers if marker in definition)
    general_score = sum(1 for marker in general_markers if marker in definition)
    return (narrow_score - general_score, len(definition))


class LawOpenApiTermClient:
    def __init__(
        self,
        *,
        oc: str | None = None,
        session: requests.Session | None = None,
        timeout_seconds: float = 5.0,
        base_url: str = LAW_OPEN_API_BASE_URL,
    ) -> None:
        self.oc = oc if oc is not None else os.getenv("LAW_OC", "")
        self.session = session or requests.Session()
        self.timeout_seconds = timeout_seconds
        self.base_url = base_url.rstrip("/")

    @property
    def enabled(self) -> bool:
        return bool(self.oc)

    def _get_json(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self.oc:
            raise LawOpenApiTermClientError("LAW_OC 환경변수가 없어 법제처 용어 API를 호출할 수 없습니다.")

        merged_params = {"OC": self.oc, "type": "JSON", **params}
        response = self.session.get(
            f"{self.base_url}/{path.lstrip('/')}",
            params=merged_params,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise LawOpenApiTermClientError("법제처 용어 API 응답이 JSON 객체가 아닙니다.")
        return payload

    def search_legal_terms(self, query: str, *, display: int = 5) -> list[str]:
        payload = self._get_json(
            "lawSearch.do",
            {
                "target": "lstrmAI",
                "query": query,
                "display": display,
            },
        )
        root = payload.get("lstrmAISearch") or {}
        terms = []
        for item in _as_list(root.get("법령용어")):
            if isinstance(item, dict):
                term = item.get("법령용어명")
                if isinstance(term, str):
                    terms.append(term)
        return list(_compact_unique(terms))

    def search_legal_dictionary_terms(self, query: str, *, display: int = 5) -> list[dict[str, Any]]:
        payload = self._get_json(
            "lawSearch.do",
            {
                "target": "lstrm",
                "query": query,
                "display": display,
            },
        )
        root = payload.get("LsTrmSearch") or {}
        rows = []
        for item in _as_list(root.get("lstrm")):
            if isinstance(item, dict):
                rows.append(item)
        return rows

    def get_legal_term_definitions(self, query: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
        rows = self.search_legal_dictionary_terms(query)
        exact_rows = [row for row in rows if row.get("법령용어명") == query]
        if not exact_rows:
            return (), ()

        term_sequences = exact_rows[0].get("법령용어ID")
        if not isinstance(term_sequences, str) or not term_sequences.strip():
            return (), ()

        payload = self._get_json(
            "lawService.do",
            {
                "target": "lstrm",
                "trmSeqs": term_sequences,
            },
        )
        root = payload.get("LsTrmService") or {}
        definitions = sorted(
            _compact_unique(
                [
                    str(item)
                    for item in _as_list(root.get("법령용어정의"))
                    if isinstance(item, str) and any("가" <= char <= "힣" for char in item)
                ]
            ),
            key=_definition_score,
        )
        sources = _compact_unique(
            [
                str(item)
                for item in _as_list(root.get("출처"))
                if isinstance(item, str)
            ]
        )
        return definitions, sources

    def get_related_daily_terms(self, legal_term: str) -> list[str]:
        payload = self._get_json(
            "lawService.do",
            {
                "target": "lstrmRlt",
                "query": legal_term,
            },
        )
        root = payload.get("lstrmRltService") or {}
        daily_terms: list[str] = []
        for legal_item in _as_list(root.get("법령용어")):
            if not isinstance(legal_item, dict):
                continue
            for related in _as_list(legal_item.get("연계용어")):
                if not isinstance(related, dict):
                    continue
                term = related.get("일상용어명")
                if isinstance(term, str):
                    daily_terms.append(term)
        return list(_compact_unique(daily_terms))

    def get_related_legal_terms(self, daily_term: str) -> list[str]:
        payload = self._get_json(
            "lawService.do",
            {
                "target": "dlytrmRlt",
                "query": daily_term,
            },
        )
        root = payload.get("dlytrmRltService") or {}
        legal_items = root.get("일상용어")
        legal_terms: list[str] = []
        for daily_item in _as_list(legal_items):
            if not isinstance(daily_item, dict):
                continue
            for related in _as_list(daily_item.get("연계용어")):
                if not isinstance(related, dict):
                    continue
                term = related.get("법령용어명")
                if isinstance(term, str):
                    legal_terms.append(term)
        return list(_compact_unique(legal_terms))

    def lookup_term(self, query: str) -> LawOpenApiTerm | None:
        legal_terms = self.search_legal_terms(query)
        related_daily_terms = self.get_related_daily_terms(query)
        definitions, definition_sources = self.get_legal_term_definitions(query)

        if not legal_terms and not related_daily_terms and not definitions:
            return None

        return LawOpenApiTerm(
            term=query,
            source="law.go.kr",
            definitions=tuple(definitions[:2]),
            definition_sources=tuple(definition_sources[:3]),
            related_daily_terms=tuple(related_daily_terms[:8]),
        )
