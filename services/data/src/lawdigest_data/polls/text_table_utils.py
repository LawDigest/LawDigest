"""ASCII-art 텍스트 표 복원 유틸리티."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

from .table_utils import extract_sample_count

_RULER_SEGMENT_RE = re.compile(r"-{3,}")
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
_WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class AsciiTotalRow:
    """ASCII-art 표의 전체 행 정보."""

    label: str
    n_completed: int | None
    percentages: List[float]
    n_weighted: int | None


def normalize_ascii_table_text(text: str) -> str:
    """ASCII 표 파싱 전 텍스트를 가볍게 정규화한다."""
    cleaned = _CONTROL_CHAR_RE.sub("", text or "")
    return cleaned.replace("\u00a0", " ").replace("\u2007", " ")


def infer_column_spans(ruler_line: str) -> List[Tuple[int, int]]:
    """구분선 라인에서 컬럼 span 목록을 추론한다."""
    return [(m.start(), m.end()) for m in _RULER_SEGMENT_RE.finditer(ruler_line or "")]


def extract_ascii_table_blocks(page_text: str) -> List[str]:
    """페이지 텍스트에서 ASCII-art 표 블록을 추출한다."""
    lines = normalize_ascii_table_text(page_text).splitlines()
    ruler_indices = [i for i, line in enumerate(lines) if len(infer_column_spans(line)) >= 2]

    if len(ruler_indices) < 2:
        return []
    return ["\n".join(lines[ruler_indices[0]:ruler_indices[-1] + 1])]


def slice_line_by_spans(line: str, spans: Sequence[Tuple[int, int]]) -> List[str]:
    """라인을 span 기준으로 잘라 컬럼 텍스트를 반환한다."""
    cells: List[str] = []
    for start, end in spans:
        cell = _slice_by_display_width(line or "", start, end)
        cells.append(cell.strip())
    return cells


def merge_multiline_header(
    lines: Iterable[str],
    spans: Sequence[Tuple[int, int]],
) -> List[str]:
    """여러 줄 헤더를 컬럼 단위로 병합한다."""
    merged: List[List[str]] = [[] for _ in spans]
    for line in lines:
        for idx, cell in enumerate(slice_line_by_spans(line, spans)):
            if cell:
                merged[idx].append(cell)

    result: List[str] = []
    for parts in merged:
        text = " ".join(parts)
        result.append(_WHITESPACE_RE.sub(" ", text).strip())
    return result


def parse_total_row(line: str, spans: Sequence[Tuple[int, int]]) -> AsciiTotalRow:
    """전체 행 라인을 파싱해 사례수와 비율을 추출한다."""
    cells = slice_line_by_spans(line, spans)
    if len(cells) < 3:
        raise ValueError("전체 행 컬럼 수가 부족합니다.")

    label = re.sub(r"\s+", "", cells[0])
    n_completed = extract_sample_count(cells[1])
    n_weighted = extract_sample_count(cells[-1])

    percentages: List[float] = []
    for cell in cells[2:-1]:
        text = cell.replace(",", "").strip()
        if not text:
            continue
        try:
            percentages.append(float(text))
        except ValueError:
            continue

    return AsciiTotalRow(
        label=label,
        n_completed=n_completed,
        percentages=percentages,
        n_weighted=n_weighted,
    )


def _slice_by_display_width(line: str, start: int, end: int) -> str:
    """표시 폭 기준으로 라인을 잘라낸다."""
    chars: List[str] = []
    col = 0
    for ch in line:
        width = _char_display_width(ch)
        next_col = col + width
        if next_col <= start:
            col = next_col
            continue
        if col >= end:
            break
        chars.append(ch)
        col = next_col
    return "".join(chars)


def _char_display_width(ch: str) -> int:
    """한글/전각 문자의 표시 폭을 2칸으로 계산한다."""
    return 2 if unicodedata.east_asian_width(ch) in {"W", "F"} else 1
