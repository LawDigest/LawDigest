from __future__ import annotations

from typing import Any

import re


SUMMARY_OPENING_TEMPLATE = "{proposer_phrase}에 의해 발의된 ‘{bill_name}’ 법안의 주요 내용은 다음과 같습니다:"
SUMMARY_LIST_GUIDELINE = (
    "3~7개 핵심 항목을 마크다운 번호 목록으로 나열하세요. "
    "각 항목은 '1. **요약:** 설명'처럼 짧은 소제목과 설명을 콜론으로 구분"
)
SUMMARY_GPT_FIELD_DESC = (
    "법안에서 달라지는 핵심 내용을 기존 형식으로 작성: "
    "'{proposer_opening}'로 시작하고, '1. **요약:** 설명' 형식의 마크다운 번호 목록을 작성한 뒤 "
    "'이 법안의 취지는 ...'로 마무리"
)


def _parse_proposer_names(raw: Any) -> list[str]:
    if not raw:
        return []

    raw_text = str(raw).strip()
    if not raw_text:
        return []

    if raw_text in {"발의자 미상", "unknown"}:
        return []

    parts = re.split(r"\s*,\s*|\s*;\s*|\s*/\s*|\s*및\s*|\n|\r|\t", raw_text)
    return [part.strip() for part in parts if part.strip()]


def build_proposer_phrase(raw: Any) -> str:
    raw_text = str(raw).strip() if raw else "발의자 미상"
    if not raw_text:
        raw_text = "발의자 미상"

    names = _parse_proposer_names(raw_text)
    count_match = re.search(r"(\d+)\s*(명|인)", raw_text)

    if count_match:
        if "등" in raw_text:
            normalized = re.sub(r"\b(\d+)\s*인\b", r"\1명", raw_text)
            normalized = re.sub(r"\b(\d+)\s*명\b", r"\1명", normalized)
            return normalized.strip()
        return f"{raw_text} 등"

    if len(names) >= 2:
        return f"{names[0]} 등 {len(names)}명"

    return f"{raw_text} 등 1명"


def build_proposer_opening_line(proposers: Any, bill_name: str) -> str:
    return SUMMARY_OPENING_TEMPLATE.format(
        proposer_phrase=build_proposer_phrase(proposers),
        bill_name=bill_name,
    )
