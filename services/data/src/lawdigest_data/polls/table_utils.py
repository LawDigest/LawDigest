"""여론조사 크로스탭 테이블 공통 유틸리티.

각 파서에서 반복되는 테이블 처리 로직을 통합한다:
  - 전체(Total) 행 탐지
  - 비율 추출 (개별 셀 / 뭉침 셀)
  - 사례수(N) 추출
  - 선택지(Option) 추출
  - 요약 컬럼 필터링
"""
from __future__ import annotations

import re
from typing import List, Optional, Sequence, Tuple

# ── 정규화 ────────────────────────────────────────────────────────────────────

# 전체 행 마커에서 제거할 문자: 공백, 대괄호, ■, ▣, ●
_TOTAL_MARKER_STRIP_RE = re.compile(r"[\s\[\]■▣●]")

# 사례수 추출: (1,007) 또는 (1007)
_SAMPLE_COUNT_RE = re.compile(r"\((\d[\d,]*)\)")

# 뭉침 비율 셀에서 개별 숫자 토큰 매칭
_FLOAT_TOKEN_RE = re.compile(r"^\d+\.?\d*$")

# ── 기본 요약 컬럼 패턴 ──────────────────────────────────────────────────────

DEFAULT_SUMMARY_PATTERNS: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\(합\)"),           # (합)
    re.compile(r"^합계$"),           # 합계
    re.compile(r"^소계$"),           # 소계
    re.compile(r"^계$"),             # 계
    re.compile(r"^T[12]$|^B[12]$"),  # T1, T2, B1, B2
    re.compile(r"\(\d\+\d\)"),       # (1+2), (3+4)
    re.compile(r"\)\s*\+\s*\("),     # (1)+(2), (3)+(4)
    re.compile(r"【.+】"),            # 【소계】
    re.compile(r"[①②③④⑤⑥⑦⑧⑨⑩]\s*\+\s*[①②③④⑤⑥⑦⑧⑨⑩]"),  # ①+②
)


def find_total_row(
    table: List[List],
    *,
    markers: Sequence[str] = ("전체",),
    col_index: int = 0,
    normalize: bool = True,
    start_row: int = 0,
) -> Optional[Tuple[int, List]]:
    """테이블에서 전체(Total) 행을 찾는다.

    Args:
        table: 2차원 테이블 데이터.
        markers: 매칭할 마커 문자열 목록 (기본 ``("전체",)``).
        col_index: 검사할 컬럼 인덱스.
        normalize: True면 공백·대괄호·■·▣ 제거 후 비교.
        start_row: 검색 시작 행 인덱스.

    Returns:
        ``(행_인덱스, 행_데이터)`` 또는 ``None``.
    """
    for i, row in enumerate(table):
        if i < start_row:
            continue
        if not row or len(row) <= col_index:
            continue
        cell = str(row[col_index] or "")
        if normalize:
            cell = _TOTAL_MARKER_STRIP_RE.sub("", cell)
        for marker in markers:
            target = _TOTAL_MARKER_STRIP_RE.sub("", marker) if normalize else marker
            if cell == target:
                return (i, row)
    return None


def extract_percentages_from_cells(
    row: List,
    start_col: int,
    end_col: Optional[int] = None,
    *,
    valid_range: Tuple[float, float] = (0.0, 100.0),
) -> List[float]:
    """개별 셀에서 비율 값을 추출한다.

    각 셀을 float 변환 시도하고, ``valid_range`` 이내인 값만 수집한다.

    Args:
        row: 테이블 행 데이터.
        start_col: 비율 추출 시작 컬럼.
        end_col: 비율 추출 종료 컬럼 (exclusive, None이면 끝까지).
        valid_range: ``(최솟값, 최댓값)`` 범위.

    Returns:
        추출된 float 리스트. 유효 값이 없으면 빈 리스트.
    """
    lo, hi = valid_range
    result: List[float] = []
    cells = row[start_col:end_col]
    for cell in cells:
        text = str(cell or "").strip()
        try:
            v = float(text)
        except ValueError:
            continue
        if lo <= v <= hi:
            result.append(v)
    return result


def extract_percentages_from_bunched_cell(
    cell_text: str,
    *,
    max_count: Optional[int] = None,
) -> List[float]:
    """공백 구분으로 뭉친 비율 문자열에서 개별 float을 추출한다.

    ``"46.3  13.9  9.8  25.1  4.9"`` → ``[46.3, 13.9, 9.8, 25.1, 4.9]``

    한글·괄호 등 비숫자 토큰을 만나면 즉시 중단한다.

    Args:
        cell_text: 공백 구분 비율 문자열.
        max_count: 최대 추출 개수 (None이면 제한 없음).

    Returns:
        추출된 float 리스트.
    """
    if not cell_text or not cell_text.strip():
        return []

    # 첫 번째 줄만 사용 (멀티라인 셀에서 하위행은 인구통계 소분류)
    first_line = cell_text.split("\n")[0].strip()
    tokens = first_line.split()

    result: List[float] = []
    for token in tokens:
        if not _FLOAT_TOKEN_RE.match(token):
            break
        result.append(float(token))
        if max_count is not None and len(result) >= max_count:
            break
    return result


def extract_sample_count(text: str) -> Optional[int]:
    """셀 텍스트에서 사례수(N)를 추출한다.

    ``"(1,007)"`` → ``1007``, ``"(1007)"`` → ``1007``.
    괄호가 없으면 순수 정수 파싱을 시도한다.

    Args:
        text: 사례수 포함 텍스트.

    Returns:
        정수 사례수 또는 ``None``.
    """
    text = str(text or "").strip()
    if not text:
        return None
    m = _SAMPLE_COUNT_RE.search(text)
    if m:
        return int(m.group(1).replace(",", ""))
    # 괄호 없이 순수 숫자
    cleaned = text.replace(",", "")
    try:
        return int(cleaned)
    except ValueError:
        return None


def extract_options_from_row(
    row: List,
    start_col: int,
    end_col: Optional[int] = None,
    *,
    skip_patterns: Sequence[re.Pattern[str]] = (),
    normalize_whitespace: bool = True,
) -> List[str]:
    """헤더 행에서 선택지 라벨을 추출한다.

    Args:
        row: 테이블 헤더 행.
        start_col: 추출 시작 컬럼.
        end_col: 추출 종료 컬럼 (exclusive, None이면 끝까지).
        skip_patterns: 건너뛸 정규식 패턴 (요약 컬럼 등).
        normalize_whitespace: True면 줄바꿈·다중 공백을 단일 공백으로.

    Returns:
        선택지 문자열 리스트.
    """
    result: List[str] = []
    cells = row[start_col:end_col]
    for cell in cells:
        text = str(cell or "").strip()
        if not text or text.lower() == "none":
            continue
        if normalize_whitespace:
            text = re.sub(r"[\n\x00\s]+", " ", text).strip()
        if any(pat.search(text) for pat in skip_patterns):
            continue
        result.append(text)
    return result


def filter_summary_columns(
    options: List[str],
    percentages: List[float],
    *,
    summary_patterns: Sequence[re.Pattern[str]] = DEFAULT_SUMMARY_PATTERNS,
) -> Tuple[List[str], List[float]]:
    """요약/소계 컬럼을 제거한다.

    ``options``와 ``percentages``는 동일 길이여야 한다.
    ``summary_patterns``에 매칭되는 선택지를 해당 비율과 함께 제거한다.

    Args:
        options: 선택지 라벨 리스트.
        percentages: 대응하는 비율 리스트.
        summary_patterns: 매칭할 정규식 패턴 시퀀스.

    Returns:
        ``(필터링된_선택지, 필터링된_비율)`` 튜플.
    """
    if len(options) != len(percentages):
        return options, percentages

    filtered_opts: List[str] = []
    filtered_pcts: List[float] = []
    for opt, pct in zip(options, percentages):
        if any(pat.search(opt) for pat in summary_patterns):
            continue
        filtered_opts.append(opt)
        filtered_pcts.append(pct)
    return filtered_opts, filtered_pcts
