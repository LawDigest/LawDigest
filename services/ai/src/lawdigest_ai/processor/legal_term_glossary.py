from __future__ import annotations

import re
from dataclasses import dataclass

from lawdigest_ai.db import get_db_connection
from lawdigest_ai.processor.law_open_api_terms import LawOpenApiTerm, LawOpenApiTermClient
from lawdigest_ai.processor.legal_term_dictionary_sync import normalize_legal_term


@dataclass(frozen=True)
class LegalTermEntry:
    term: str
    definition: str
    aliases: tuple[str, ...] = ()
    explain: bool = True


LAW_OPEN_API_REFERENCES = (
    "법령용어 목록: https://www.law.go.kr/DRF/lawSearch.do?target=lstrm",
    "법령용어 상세 정의: https://www.law.go.kr/DRF/lawService.do?target=lstrm",
)

LEGAL_TERM_GLOSSARY = (
    LegalTermEntry(
        term="청문 규정",
        aliases=("청문", "청문 절차", "청문 규정"),
        definition="처분을 받기 전에 당사자가 설명하고 반론할 수 있는 절차에요.",
    ),
    LegalTermEntry(
        term="과태료",
        aliases=("과태료",),
        definition="행정질서 위반에 대해 부과하는 금전 제재에요. 형사처벌과는 달라요.",
    ),
    LegalTermEntry(
        term="위임·위탁",
        aliases=("위임·위탁", "위임", "위탁"),
        definition="행정기관의 권한이나 업무 일부를 다른 기관이 맡아 처리하게 하는 방식이에요.",
    ),
)

COMMON_TERMS_WITHOUT_EXPLANATION = ("허위정보", "허위정보 유포", "필수정보", "표시·광고")

LEGAL_TERM_CANDIDATE_SUFFIXES = (
    "감사",
    "보고서",
    "요구",
    "위원회",
    "시설",
    "시설물",
    "부지",
    "재산",
    "점유",
    "사용료",
    "대부료",
    "변상금",
    "수급자",
    "주차장",
    "분권",
    "자치",
    "행정구",
    "청문",
    "과태료",
    "위임",
    "위탁",
    "양여",
)

LEGAL_TERM_CANDIDATE_STOPWORDS = {
    "제안이유",
    "주요내용",
    "현행법",
    "현행",
    "개정",
    "규정",
    "경우",
    "내용",
    "법안",
    "법률안",
    "개정법률안",
}

LEGAL_TERM_PARTICLES = (
    "으로써",
    "으로서",
    "에서는",
    "에게는",
    "부터",
    "까지",
    "으로",
    "로서",
    "로써",
    "에는",
    "에서",
    "에게",
    "하고",
    "하며",
    "하게",
    "하도록",
    "하여",
    "하는",
    "된다",
    "되어",
    "되며",
    "되지",
    "이며",
    "이고",
    "라는",
    "이라",
    "은",
    "는",
    "이",
    "가",
    "을",
    "를",
    "의",
    "와",
    "과",
    "도",
    "만",
    "등",
)


def _matches(text: str, entry: LegalTermEntry) -> bool:
    return any(alias in text for alias in entry.aliases)


def _matched_static_entries(text: str) -> list[LegalTermEntry]:
    return [entry for entry in LEGAL_TERM_GLOSSARY if _matches(text, entry)]


def _strip_particle(value: str) -> str:
    token = value.strip(" .,;:()[]「」‘’“”\"'")
    for particle in LEGAL_TERM_PARTICLES:
        if len(token) > len(particle) + 1 and token.endswith(particle):
            return token[: -len(particle)]
    return token


def _extract_legal_term_candidates(text: str, *, max_terms: int = 24) -> list[str]:
    normalized = re.sub(r"\s+", " ", text.replace("ㆍ", "·"))
    terms: list[str] = []
    seen: set[str] = set(COMMON_TERMS_WITHOUT_EXPLANATION)

    def add(term: str) -> None:
        term = _strip_particle(term)
        if (
            len(term) < 3
            or term in seen
            or term in LEGAL_TERM_CANDIDATE_STOPWORDS
            or not re.fullmatch(r"[가-힣][가-힣A-Za-z0-9·]{2,15}", term)
        ):
            return
        seen.add(term)
        terms.append(term)

    for token in re.split(r"[^가-힣A-Za-z0-9·]+", normalized):
        add(token)
        if len(terms) >= max_terms:
            break

    return terms


def _lookup_law_open_api_terms(
    terms: list[str],
    term_client: LawOpenApiTermClient | None,
) -> list[LawOpenApiTerm]:
    client = term_client or LawOpenApiTermClient()
    if not client.enabled:
        return []

    results: list[LawOpenApiTerm] = []
    for term in terms:
        try:
            result = client.lookup_term(term)
        except Exception:
            continue
        if result is not None and result.definitions:
            results.append(result)
    return results


def _lookup_local_dictionary_terms(terms: list[str], *, mode: str = "prod") -> list[LawOpenApiTerm]:
    normalized_terms = [normalize_legal_term(term) for term in terms]
    normalized_terms = [term for index, term in enumerate(normalized_terms) if term and term not in normalized_terms[:index]]
    if not normalized_terms:
        return []

    placeholders = ", ".join(["%s"] * len(normalized_terms))
    query = f"""
        SELECT term, definition
        FROM LegalTermDictionary
        WHERE enabled = TRUE
          AND normalized_term IN ({placeholders})
        ORDER BY FIELD(normalized_term, {placeholders})
    """
    try:
        conn = get_db_connection(mode=mode)
        try:
            with conn.cursor() as cur:
                cur.execute(query, [*normalized_terms, *normalized_terms])
                rows = cur.fetchall()
        finally:
            conn.close()
    except Exception:
        return []

    return [
        LawOpenApiTerm(
            term=str(row["term"]),
            source="lawdigest-local-dictionary",
            definitions=(str(row["definition"]),),
        )
        for row in rows
        if row.get("term") and row.get("definition")
    ]


def build_legal_term_glossary_context(text: str, term_client: LawOpenApiTermClient | None = None) -> str:
    direct_matches = _matched_static_entries(text)
    direct_terms = [entry.aliases[0] if entry.aliases else entry.term for entry in direct_matches]
    candidate_terms = [*direct_terms, *_extract_legal_term_candidates(text)]
    local_terms = _lookup_local_dictionary_terms(candidate_terms)
    local_normalized = {normalize_legal_term(item.term) for item in local_terms}
    api_candidate_terms = [term for term in candidate_terms if normalize_legal_term(term) not in local_normalized]
    api_terms = _lookup_law_open_api_terms(api_candidate_terms, term_client)
    dictionary_terms = [*local_terms, *api_terms]
    matched_entries = direct_matches or ([] if dictionary_terms else list(LEGAL_TERM_GLOSSARY))

    lines = [
        "법률·행정용어 풀이 사전:",
        "- 아래 사전에 있는 어려운 법률·행정용어가 본문에 나오면 첫 등장 한 번만 `{{용어:뜻}}` 툴팁 표기로 감싸세요.",
    ]
    if dictionary_terms:
        lines.append("- 아래 `법제처 용어사전 조회 결과`는 Lawdigest 로컬 사전 또는 실제 법제처 Open API 정의 조회 결과입니다.")
    else:
        lines.append("- 아래 `정적 보조 사전`은 API 조회 결과가 아니라 Lawdigest가 관리하는 fallback 설명입니다.")
    lines.append("- 법제처 API 참조:")
    lines.extend(f"  - {reference}" for reference in LAW_OPEN_API_REFERENCES)
    if dictionary_terms:
        lines.append("- 법제처 용어사전 조회 결과:")
        for item in dictionary_terms:
            definitions = item.definitions[0]
            lines.append(f"  - {item.term}: 뜻={definitions}")
    if matched_entries:
        lines.append("- 설명할 용어:")
        lines.extend(f"  - {entry.term}: {entry.definition}" for entry in matched_entries if entry.explain)
    lines.append("- 설명하지 않을 용어:")
    lines.extend(f"  - {term}" for term in COMMON_TERMS_WITHOUT_EXPLANATION)
    return "\n".join(lines)
