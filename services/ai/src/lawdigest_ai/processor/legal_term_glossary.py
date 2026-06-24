from __future__ import annotations

from dataclasses import dataclass

from lawdigest_ai.processor.law_open_api_terms import LawOpenApiTerm, LawOpenApiTermClient


@dataclass(frozen=True)
class LegalTermEntry:
    term: str
    definition: str
    aliases: tuple[str, ...] = ()
    explain: bool = True


LAW_OPEN_API_REFERENCES = (
    "법령용어 목록: https://www.law.go.kr/DRF/lawSearch.do?target=lstrm",
    "법령정보지식베이스 법령용어: https://www.law.go.kr/DRF/lawSearch.do?target=lstrmAI",
    "법령용어-일상용어 연계: https://www.law.go.kr/DRF/lawService.do?target=lstrmRlt",
    "일상용어-법령용어 연계: https://www.law.go.kr/DRF/lawService.do?target=dlytrmRlt",
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


def _matches(text: str, entry: LegalTermEntry) -> bool:
    return any(alias in text for alias in entry.aliases)


def _matched_static_entries(text: str) -> list[LegalTermEntry]:
    return [entry for entry in LEGAL_TERM_GLOSSARY if _matches(text, entry)]


def _lookup_law_open_api_terms(
    entries: list[LegalTermEntry],
    term_client: LawOpenApiTermClient | None,
) -> list[LawOpenApiTerm]:
    client = term_client or LawOpenApiTermClient()
    if not client.enabled:
        return []

    results: list[LawOpenApiTerm] = []
    for entry in entries:
        try:
            result = client.lookup_term(entry.aliases[0] if entry.aliases else entry.term)
        except Exception:
            continue
        if result is not None:
            results.append(result)
    return results


def build_legal_term_glossary_context(text: str, term_client: LawOpenApiTermClient | None = None) -> str:
    direct_matches = _matched_static_entries(text)
    matched_entries = direct_matches or list(LEGAL_TERM_GLOSSARY)
    api_terms = _lookup_law_open_api_terms(direct_matches, term_client)

    lines = [
        "법률·행정용어 풀이 사전:",
        "- 설명 불릿은 아래 사전에 있는 어려운 법률·행정용어가 본문에 나올 때만 붙이세요.",
    ]
    if api_terms:
        lines.append("- 아래 `법제처 API 조회 결과`는 실제 법제처 Open API 호출 결과입니다.")
    else:
        lines.append("- 아래 `정적 보조 사전`은 API 조회 결과가 아니라 Lawdigest가 관리하는 fallback 설명입니다.")
    lines.append("- 법제처 API 참조:")
    lines.extend(f"  - {reference}" for reference in LAW_OPEN_API_REFERENCES)
    if api_terms:
        lines.append("- 법제처 API 조회 결과:")
        for item in api_terms:
            definitions = " / ".join(item.definitions) if item.definitions else "없음"
            related_daily_terms = ", ".join(item.related_daily_terms) if item.related_daily_terms else "없음"
            lines.append(f"  - {item.term}: 뜻={definitions}; 일상어 연계어={related_daily_terms}")
    lines.append("- 설명할 용어:")
    lines.extend(f"  - {entry.term}: {entry.definition}" for entry in matched_entries if entry.explain)
    lines.append("- 설명하지 않을 용어:")
    lines.extend(f"  - {term}" for term in COMMON_TERMS_WITHOUT_EXPLANATION)
    return "\n".join(lines)
