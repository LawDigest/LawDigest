"""PDF 패턴 탐지기 — 파서 개발에 필요한 핵심 구조 정보를 추출한다."""
from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    HeaderRowAnalysis,
    MarkerOccurrence,
    PageContinuity,
    QuestionBlockPatterns,
    RatioFormat,
    TableStructure,
    TotalRowMarkers,
)
from .pdf_analyzer import AnalyzedPdf

# ── 질문 블록 마커 패턴 사전 ──────────────────────────────────────────────────
# (display_name, regex, numbering_style)
_Q_MARKER_PATTERNS: List[Tuple[str, str, str]] = [
    ("[표N]",   r"\[표\s*\d+\]",                     "bracket_pyo"),
    ("표 N",    r"(?m)^표\s*\d+\s*\n",               "pyo_newline"),   # 윈지코리아 등
    ("[문N]",   r"\[문\s*\d+\]",                     "bracket_mun"),
    ("[QN]",    r"\[Q\s*\d+\]",                     "bracket_Q"),
    ("QN.",     r"\bQ\s*\d+\s*[.。]",               "Q_dot"),
    ("N번)",    r"\b\d{1,2}번\s*\)",                 "N_beon_paren"),
    ("N)",      r"(?m)^\s*\d{1,2}\s*\)\s+\S",       "N_paren"),
    ("N.",      r"(?m)^\s*\d{1,2}\s*\.\s+[가-힣A-Z]","N_dot"),
    ("문N.",    r"문\s*\d+\s*[.。]",                 "mun_dot"),
    ("SQ N.",   r"SQ\s*\d+\s*[.。]",                "SQ_dot"),
    ("문N)",    r"문\s*\d+\s*\)",                    "mun_paren"),
]

# ── 전체/합계 행 마커 패턴 사전 ────────────────────────────────────────────────
_TOTAL_MARKER_PATTERNS: List[Tuple[str, str]] = [
    ("▣ 전체 ▣",   r"▣\s*전체\s*▣"),
    ("■ 전체 ■",   r"■\s*전체\s*■"),
    ("□ 전체 □",   r"□\s*전체\s*□"),
    ("● 전체 ●",   r"●\s*전체\s*●"),
    ("전체",        r"(?m)^\s*전체\s"),
    ("계",          r"(?m)^\s*계\s"),
    ("합계",        r"(?m)^\s*합계\s"),
    ("전 체",       r"전\s+체"),
]

# ── 테이블 셀 전체행 마커 — 텍스트 기반 패턴과 별도로 셀 raw 값을 정규화하여 매칭
# re.sub(r"[\s\[\]]", "", cell) == "전체" 이면 전체행으로 판단
_TOTAL_CELL_NORMALIZER = re.compile(r"[\s\[\]]")

# ── N값 포맷 패턴 ───────────────────────────────────────────────────────────────
_N_FORMAT_PATTERNS: List[Tuple[str, str, str]] = [
    ("parenthesized_comma",  r"\(\d{1,3}(?:,\d{3})+\)",   "(1,000)"),
    ("parenthesized_plain",  r"\(\d{3,4}\)",               "(1000)"),
    ("plain_comma",          r"(?<!\()\d{1,3}(?:,\d{3})+(?!\))", "1,000"),
    ("plain_plain",          r"(?<!\()\b\d{3,4}\b(?!\))",  "1000"),
]

# ── 비율 숫자 패턴 ──────────────────────────────────────────────────────────────
_RATIO_RE = re.compile(r"\b(\d{1,3})\.(\d)\b")   # e.g. 45.2
_BUNDLED_RATIO_RE = re.compile(
    r"(\d{1,3}\.\d[\s,]*){3,}"    # 공백/쉼표로 연결된 3개 이상 비율
)

# ── 페이지 연속성 신호 ──────────────────────────────────────────────────────────
_CONTINUATION_SIGNALS: List[Tuple[str, str]] = [
    ("consecutive_title", "동일 질문 제목이 연속 페이지에 반복"),
    ("headerless_table",  "헤더 없는 테이블이 후속 페이지에 출현"),
    ("continued_marker",  "'계속', '(계속)', '(이하 계속)' 등 연속 마커"),
]
_CONTINUED_RE = re.compile(r"계속|이하\s*계속|다음\s*페이지", re.IGNORECASE)


class PatternDetector:
    """AnalyzedPdf에서 파서 개발에 필요한 패턴을 탐지한다."""

    def detect_question_blocks(self, analyzed: AnalyzedPdf) -> QuestionBlockPatterns:
        """질문 블록 구분 마커를 탐지한다.

        테이블이 있는 페이지(크로스탭)와 없는 페이지(보고서 본문)를 분리하여 탐지한다.
        크로스탭 페이지에서 발견된 마커를 우선 순위로 사용한다.
        """
        text = analyzed.full_text
        if not text:
            return QuestionBlockPatterns()

        # 테이블 있는 페이지 / 없는 페이지 텍스트 분리
        crosstab_texts: List[str] = []
        text_only_texts: List[str] = []
        for i, (_, tables, _) in enumerate(analyzed.pages_data):
            page_text = analyzed.per_page_texts[i] if i < len(analyzed.per_page_texts) else ""
            if tables:
                crosstab_texts.append(page_text)
            else:
                text_only_texts.append(page_text)

        crosstab_full = "\n".join(crosstab_texts)
        text_only_full = "\n".join(text_only_texts)

        detected: List[MarkerOccurrence] = []
        for display, regex, style in _Q_MARKER_PATTERNS:
            matches_crosstab = list(re.finditer(regex, crosstab_full))
            matches_text_only = list(re.finditer(regex, text_only_full))
            matches_all = list(re.finditer(regex, text))

            if not matches_all:
                continue

            # 크로스탭 페이지에서 발견된 경우 우선 표시
            source_label = ""
            if matches_crosstab and not matches_text_only:
                source_label = " [크로스탭 전용]"
            elif matches_text_only and not matches_crosstab:
                source_label = " [본문 전용 — 크로스탭 파서에서 사용 불가]"
            elif matches_crosstab and matches_text_only:
                source_label = " [크로스탭+본문 혼재]"

            # 페이지별 매핑
            example_pages: List[int] = []
            for i, page_text in enumerate(analyzed.per_page_texts, start=1):
                if re.search(regex, page_text):
                    example_pages.append(i)

            # 대표 예시 (크로스탭 페이지 우선, 최대 3개)
            examples: List[str] = []
            source_text = crosstab_full if matches_crosstab else text
            for m in list(re.finditer(regex, source_text))[:3]:
                start = max(0, m.start())
                end = min(len(source_text), m.end() + 40)
                snippet = source_text[start:end].replace("\n", " ").strip()
                examples.append(snippet)

            detected.append(MarkerOccurrence(
                pattern=display + source_label,
                regex=regex,
                occurrences=len(matches_all),
                example_pages=list(dict.fromkeys(example_pages))[:5],
                examples=examples,
            ))

        # 크로스탭 전용 마커 우선, 그다음 출현 횟수 기준 정렬
        detected.sort(
            key=lambda m: (
                0 if "크로스탭 전용" in m.pattern else
                1 if "혼재" in m.pattern else
                2,
                -m.occurrences,
            )
        )

        # 질문 수 추정: 크로스탭 전용 마커 중 1위 기준
        estimated = 0
        numbering_style = "unknown"
        if detected:
            # 크로스탭 전용 마커 우선
            best = next(
                (m for m in detected if "크로스탭 전용" in m.pattern),
                detected[0],
            )
            estimated = best.occurrences
            base_pattern = best.pattern.split(" [")[0]
            for display, r, s in _Q_MARKER_PATTERNS:
                if display == base_pattern:
                    numbering_style = s
                    break

        return QuestionBlockPatterns(
            detected_markers=detected,
            question_numbering_style=numbering_style,
            estimated_question_count=estimated,
        )

    def detect_total_row_markers(self, analyzed: AnalyzedPdf) -> TotalRowMarkers:
        """전체/합계 행 마커 및 N값 포맷을 탐지한다.

        텍스트 기반 탐지 외에, 실제 테이블 셀(row[0])에서의 raw 값도 수집한다.
        텍스트 렌더링과 셀 추출 결과가 다를 수 있으므로 (예: '전체' vs '[ 전 체 ]')
        셀 기반 결과를 별도로 제공한다.
        """
        text = analyzed.full_text
        if not text:
            return TotalRowMarkers()

        detected: List[MarkerOccurrence] = []
        for display, regex in _TOTAL_MARKER_PATTERNS:
            matches = list(re.finditer(regex, text, re.MULTILINE))
            if not matches:
                continue

            example_pages: List[int] = []
            for i, page_text in enumerate(analyzed.per_page_texts, start=1):
                if re.search(regex, page_text, re.MULTILINE):
                    example_pages.append(i)

            examples: List[str] = []
            for m in matches[:3]:
                start = max(0, m.start())
                end = min(len(text), m.end() + 60)
                snippet = text[start:end].replace("\n", " ").strip()
                examples.append(snippet)

            detected.append(MarkerOccurrence(
                pattern=display,
                regex=regex,
                occurrences=len(matches),
                example_pages=list(dict.fromkeys(example_pages))[:5],
                examples=examples,
            ))

        # 테이블 셀 기반 전체행 마커 탐지 (row[0] raw 값 수집)
        # 파서가 실제로 보는 셀 값이므로 텍스트 기반보다 더 정확하다
        cell_total_forms: Dict[str, List[int]] = {}  # raw_value → 등장 페이지 목록
        for page_num, (_, tables, _) in enumerate(analyzed.pages_data, start=1):
            for tbl in tables:
                for row in tbl:
                    if not row or row[0] is None:
                        continue
                    cell_val = str(row[0]).strip()
                    normalized = _TOTAL_CELL_NORMALIZER.sub("", cell_val)
                    if normalized == "전체":
                        if cell_val not in cell_total_forms:
                            cell_total_forms[cell_val] = []
                        if page_num not in cell_total_forms[cell_val]:
                            cell_total_forms[cell_val].append(page_num)

        # 셀 기반 탐지 결과를 detected에 추가 (텍스트 기반에 없는 변형만)
        existing_patterns = {m.pattern for m in detected}
        for cell_val, pages in sorted(cell_total_forms.items(), key=lambda x: -len(x[1])):
            marker_label = f"셀:{repr(cell_val)}"
            if marker_label not in existing_patterns:
                detected.append(MarkerOccurrence(
                    pattern=marker_label,
                    regex="",  # 셀 기반은 regex 없음
                    occurrences=len(pages),
                    example_pages=pages[:5],
                    examples=[f"row[0] = {repr(cell_val)}"],
                ))

        detected.sort(key=lambda m: m.occurrences, reverse=True)

        # N값 포맷 탐지
        n_format = "unknown"
        n_examples: List[str] = []
        for fmt_name, fmt_regex, _ in _N_FORMAT_PATTERNS:
            matches = re.findall(fmt_regex, text)
            if matches:
                n_format = fmt_name
                n_examples = list(dict.fromkeys(matches))[:5]
                break

        return TotalRowMarkers(
            detected_markers=detected,
            n_format=n_format,
            n_examples=n_examples,
        )

    def analyze_table_structure(self, analyzed: AnalyzedPdf) -> TableStructure:
        """테이블 구조(헤더, meta 컬럼, 선택지, 비율 위치)를 분석한다."""
        pages_with = sum(1 for p in analyzed.pages if p.table_count > 0)
        pages_without = len(analyzed.pages) - pages_with

        # 모든 테이블 수집 (pages_data에서)
        all_tables: List[List[List[Any]]] = []
        for _, tables, _ in analyzed.pages_data:
            all_tables.extend(tables)

        if not all_tables:
            return TableStructure(
                pages_with_tables=pages_with,
                pages_without_tables=pages_without,
            )

        # 전형적 형태 추정
        shapes = [(len(t), max(len(r) for r in t)) for t in all_tables if t]
        if shapes:
            row_counts = [s[0] for s in shapes]
            col_counts = [s[1] for s in shapes]
            typical_rows = Counter(row_counts).most_common(1)[0][0]
            typical_cols = Counter(col_counts).most_common(1)[0][0]
        else:
            typical_rows, typical_cols = 0, 0

        # 헤더 행 분석 (충분한 컬럼이 있는 테이블에서 첫 행 분석)
        header_analysis = self._analyze_header_rows(all_tables)

        # 비율 위치 판별
        ratio_location, ratio_fmt, bundled, bundled_ex = self._detect_ratio_location(analyzed)

        return TableStructure(
            pages_with_tables=pages_with,
            pages_without_tables=pages_without,
            typical_shape={"rows": typical_rows, "cols": typical_cols},
            header_row_analysis=header_analysis,
            ratio_data_location=ratio_location,
            ratio_format=ratio_fmt,
            ratio_cell_bundled=bundled,
            bundled_example=bundled_ex,
        )

    def detect_page_continuity(self, analyzed: AnalyzedPdf) -> PageContinuity:
        """페이지 간 질문 연속성을 탐지한다."""
        signals: List[str] = []
        affected = 0

        texts = analyzed.per_page_texts

        # 신호 1: '계속' 마커
        for text in texts:
            if _CONTINUED_RE.search(text):
                signals.append("continued_marker")
                break

        # 신호 2: 헤더 없는 테이블 (컬럼 수가 동일하지만 첫 행이 숫자로 시작)
        prev_cols = 0
        for _, tables, _ in analyzed.pages_data:
            for tbl in tables:
                if not tbl:
                    continue
                first_row = [str(c or "").strip() for c in tbl[0]]
                cols = len(first_row)
                # 첫 셀이 비어있거나 숫자면 헤더 없는 테이블 가능성
                if cols == prev_cols and (not first_row[0] or first_row[0].replace(",", "").isdigit()):
                    signals.append("headerless_table")
                    affected += 1
                    break
                prev_cols = cols

        # 신호 3: 연속 페이지에서 동일 패턴 반복 (질문 제목이 2페이지 이상에 걸침)
        q_pattern = re.compile(r"\[표\s*(\d+)\]|\[Q\s*(\d+)\]|\[문\s*(\d+)\]")
        page_q_sets: List[set] = []
        for text in texts:
            nums = set(m.group(1) or m.group(2) or m.group(3) for m in q_pattern.finditer(text))
            page_q_sets.append(nums)

        for i in range(len(page_q_sets) - 1):
            overlap = page_q_sets[i] & page_q_sets[i + 1]
            if overlap:
                signals.append("consecutive_title")
                affected += len(overlap)
                break

        unique_signals = list(dict.fromkeys(signals))
        return PageContinuity(
            multi_page_questions_detected=bool(unique_signals),
            continuity_signals=unique_signals,
            affected_question_count=affected,
        )

    # ── 내부 헬퍼 ──────────────────────────────────────────────────────────────

    def _analyze_header_rows(self, tables: List[List[List[Any]]]) -> HeaderRowAnalysis:
        """테이블 헤더 행을 분석하여 meta 컬럼 수, 선택지 시작 위치 등을 추출한다."""
        # 충분한 컬럼이 있는 테이블만 분석 (최소 5컬럼)
        candidate_tables = [t for t in tables if t and max(len(r) for r in t) >= 5]
        if not candidate_tables:
            return HeaderRowAnalysis()

        # 헤더 행 후보 수집 (첫 행 또는 두 번째 행)
        header_rows: List[List[str]] = []
        for tbl in candidate_tables[:10]:  # 최대 10개 테이블만 분석
            if tbl:
                row = [str(c or "").strip() for c in tbl[0]]
                header_rows.append(row)

        if not header_rows:
            return HeaderRowAnalysis()

        # 가장 긴 헤더 기준
        longest = max(header_rows, key=len)

        # meta 컬럼 탐지: 앞에서부터 비어있거나 숫자/단위가 아닌 셀이 meta
        # "전체", "구분", "사례수", "(명)", 빈칸 등
        _META_HINTS = {"전체", "구분", "사례수", "(명)", "명", "", "계", "N", "n"}
        _UNIT_RE = re.compile(r"^\d|^%|^\(|^명$|^N$|^n$|^계$")

        meta_count = 0
        for cell in longest:
            if cell in _META_HINTS or _UNIT_RE.match(cell) or not cell:
                meta_count += 1
            else:
                break

        # 최소 1개는 meta로 간주
        meta_count = max(1, meta_count)

        # 선택지 컬럼 추출 (meta 이후 ~ 마지막 2개 전까지)
        option_start = meta_count
        option_end = max(option_start + 1, len(longest) - 2)
        options = [c for c in longest[option_start:option_end] if c and not _UNIT_RE.match(c)]

        # summary 컬럼 탐지 (끝에서 1~2개: ①+②, 계, T1B2 등)
        _SUMMARY_RE = re.compile(r"[①②③④⑤⑥⑦⑧⑨⑩]\s*\+|T\dB\d|소계|정계|합계|순긍정|순부정")
        summary_cols = [c for c in longest[-3:] if c and _SUMMARY_RE.search(c)]

        return HeaderRowAnalysis(
            meta_cols_count=meta_count,
            meta_col_labels=longest[:meta_count],
            option_cols_start_index=option_start,
            option_examples=options[:6],
            has_summary_cols=bool(summary_cols),
            summary_col_patterns=summary_cols,
        )

    def _detect_ratio_location(
        self, analyzed: AnalyzedPdf
    ) -> Tuple[str, RatioFormat, bool, Optional[str]]:
        """비율 데이터 위치와 포맷을 판별한다.

        Returns:
            (location, ratio_format, is_bundled, bundled_example)
        """
        text = analyzed.full_text
        ratio_matches = _RATIO_RE.findall(text)

        # 테이블 셀에서 비율 탐지
        cell_ratios: List[str] = []
        text_ratios: List[str] = []

        for _, tables, full_text in analyzed.pages_data:
            for tbl in tables:
                for row in tbl:
                    for cell in row:
                        cell_str = str(cell or "").strip()
                        if _RATIO_RE.match(cell_str) and "." in cell_str:
                            cell_ratios.append(cell_str)

            # 테이블 외부 텍스트에서 비율 탐지
            outside = analyzed.pages_data[0][0] if analyzed.pages_data else ""
            if _BUNDLED_RATIO_RE.search(full_text):
                text_ratios.append("bundled")

        # 뭉친 비율 탐지
        bundled_match = _BUNDLED_RATIO_RE.search(text)
        bundled_example: Optional[str] = None
        is_bundled = False
        if bundled_match:
            is_bundled = True
            bundled_example = text[bundled_match.start():bundled_match.end() + 20].replace("\n", " ")[:80]

        # 위치 판정
        if len(cell_ratios) > 5 and not is_bundled:
            location = "table_cell"
        elif is_bundled and len(cell_ratios) <= 5:
            location = "text_bundled"
        elif len(cell_ratios) > 5 and is_bundled:
            location = "mixed"
        elif ratio_matches:
            location = "text_bundled"
        else:
            location = "unknown"

        # 비율 포맷 분석
        decimal_counts: List[int] = []
        example_strs: List[str] = []
        sample = cell_ratios[:20] if cell_ratios else [f"{a}.{b}" for a, b in ratio_matches[:20]]
        for val in sample:
            if "." in val:
                decimals = len(val.split(".", 1)[1])
                decimal_counts.append(decimals)
                example_strs.append(val)

        decimal_places = Counter(decimal_counts).most_common(1)[0][0] if decimal_counts else 1

        ratio_fmt = RatioFormat(
            decimal_places=decimal_places,
            is_percentage=True,
            examples=example_strs[:5],
        )

        return location, ratio_fmt, is_bundled, bundled_example
