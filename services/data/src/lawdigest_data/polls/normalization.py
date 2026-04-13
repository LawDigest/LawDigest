"""여론조사 적재용 정규화 규칙."""

from __future__ import annotations

from typing import Final

CANONICAL_PARTY_NAMES: Final[tuple[str, ...]] = (
    "더불어민주당",
    "국민의힘",
    "개혁신당",
    "조국혁신당",
    "진보당",
    "정의당",
    "기본소득당",
    "새로운미래",
    "자유통일당",
    "민주노동당",
    "노동당",
    "녹색당",
    "무소속",
)


def _collapse_spaces(value: str | None) -> str:
    return "" if value is None else "".join(value.split())


def normalize_party_name(value: str | None) -> str:
    normalized = (value or "").strip()
    if not normalized or normalized == "undecided":
        return normalized

    collapsed = _collapse_spaces(normalized)
    for canonical_name in CANONICAL_PARTY_NAMES:
        if _collapse_spaces(canonical_name) == collapsed:
            return canonical_name
    return normalized
