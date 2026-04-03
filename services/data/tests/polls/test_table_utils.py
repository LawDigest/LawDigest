"""table_utils 공통 유틸리티 단위 테스트."""
from __future__ import annotations

import re

from lawdigest_data.polls.table_utils import (
    extract_options_from_row,
    extract_percentages_from_bunched_cell,
    extract_percentages_from_cells,
    extract_sample_count,
    filter_summary_columns,
    find_total_row,
)


# ─── find_total_row ──────────────────────────────────────────────────────────


class TestFindTotalRow:
    """전체(Total) 행 탐지 테스트."""

    def test_exact_match(self) -> None:
        table = [["구분"], ["전체", "(1007)", "52.4"]]
        result = find_total_row(table)
        assert result is not None
        idx, row = result
        assert idx == 1
        assert row[0] == "전체"

    def test_spaced_marker(self) -> None:
        """'전 체' (공백 포함) 매칭."""
        table = [[""], ["전 체", "(1002)", "46.3"]]
        result = find_total_row(table)
        assert result is not None
        assert result[0] == 1

    def test_bracketed_spaced_marker(self) -> None:
        """'[ 전 체 ]' (대괄호 + 공백) 매칭."""
        table = [["조사완료"], ["[ 전 체 ]", "(1,007)", "100.0"]]
        result = find_total_row(table)
        assert result is not None
        assert result[0] == 1

    def test_embrain_marker(self) -> None:
        """'■ 전체 ■' (EmbrainPublic 스타일) 매칭."""
        table = [[""], ["■ 전체 ■", "(800)", "100.0"]]
        result = find_total_row(table)
        assert result is not None

    def test_korean_research_marker(self) -> None:
        """'▣ 전체 ▣' (KoreanResearch 스타일) 매칭."""
        table = [[""], ["▣ 전체 ▣", "(1000)", "100.0"]]
        result = find_total_row(table)
        assert result is not None

    def test_signal_pulse_spaced(self) -> None:
        """'▣ 전 체 ▣' (SignalPulse 스타일) 매칭."""
        table = [[""], ["▣ 전 체 ▣", "(500)", "100.0"]]
        result = find_total_row(table)
        assert result is not None

    def test_hapgye_marker(self) -> None:
        """'합계' 마커 매칭."""
        table = [["구분"], ["합계", "(300)"]]
        result = find_total_row(table, markers=("합계",))
        assert result is not None

    def test_no_match_returns_none(self) -> None:
        table = [["구분", "사례수"], ["남성", "(522)"], ["여성", "(485)"]]
        assert find_total_row(table) is None

    def test_empty_table(self) -> None:
        assert find_total_row([]) is None

    def test_start_row_skips_earlier(self) -> None:
        table = [["전체", "skip"], ["다른행"], ["전체", "use this"]]
        result = find_total_row(table, start_row=1)
        assert result is not None
        assert result[0] == 2

    def test_normalize_false(self) -> None:
        """normalize=False이면 정확히 일치해야 한다."""
        table = [[""], ["전 체", "(1002)"]]
        assert find_total_row(table, normalize=False) is None
        assert find_total_row(table, normalize=False, markers=("전 체",)) is not None

    def test_col_index(self) -> None:
        """col_index 지정 시 해당 컬럼에서 검색."""
        table = [["a", "구분"], ["b", "전체"]]
        assert find_total_row(table, col_index=0) is None
        result = find_total_row(table, col_index=1)
        assert result is not None
        assert result[0] == 1

    def test_none_cell_skipped(self) -> None:
        table = [[None], [None, "전체"]]
        assert find_total_row(table) is None  # col_index=0 은 None


# ─── extract_percentages_from_cells ──────────────────────────────────────────


class TestExtractPercentagesFromCells:
    """개별 셀 비율 추출 테스트."""

    def test_basic(self) -> None:
        row = ["전체", None, "(1007)", "(1007)", "52.4", "30.0", "2.2"]
        result = extract_percentages_from_cells(row, start_col=4)
        assert result == [52.4, 30.0, 2.2]

    def test_skips_non_numeric(self) -> None:
        row = ["전체", None, "(1007)", "(1007)", "52.4", "abc", "30.0"]
        result = extract_percentages_from_cells(row, start_col=4)
        assert result == [52.4, 30.0]

    def test_skips_none_cells(self) -> None:
        row = ["전체", None, None, None, "52.4", None, "30.0"]
        result = extract_percentages_from_cells(row, start_col=4)
        assert result == [52.4, 30.0]

    def test_valid_range(self) -> None:
        row = ["전체", "150.0", "52.4", "-5.0", "30.0"]
        result = extract_percentages_from_cells(row, start_col=1)
        assert result == [52.4, 30.0]

    def test_end_col(self) -> None:
        row = ["전체", "10.0", "20.0", "30.0", "100.0"]
        result = extract_percentages_from_cells(row, start_col=1, end_col=4)
        assert result == [10.0, 20.0, 30.0]

    def test_empty_row(self) -> None:
        assert extract_percentages_from_cells([], start_col=0) == []

    def test_zero_and_hundred_included(self) -> None:
        row = ["전체", "0.0", "100.0", "50.0"]
        result = extract_percentages_from_cells(row, start_col=1)
        assert result == [0.0, 100.0, 50.0]


# ─── extract_percentages_from_bunched_cell ───────────────────────────────────


class TestExtractPercentagesFromBunchedCell:
    """뭉침 비율 셀 추출 테스트."""

    def test_basic(self) -> None:
        result = extract_percentages_from_bunched_cell("46.3 13.9 9.8 25.1 4.9")
        assert result == [46.3, 13.9, 9.8, 25.1, 4.9]

    def test_stops_at_korean(self) -> None:
        """한글 토큰에서 중단."""
        result = extract_percentages_from_bunched_cell("46.3 13.9 성별 남성")
        assert result == [46.3, 13.9]

    def test_stops_at_parenthesized(self) -> None:
        """괄호 토큰에서 중단."""
        result = extract_percentages_from_bunched_cell("46.3 13.9 (1002)")
        assert result == [46.3, 13.9]

    def test_empty_string(self) -> None:
        assert extract_percentages_from_bunched_cell("") == []

    def test_whitespace_only(self) -> None:
        assert extract_percentages_from_bunched_cell("   ") == []

    def test_max_count(self) -> None:
        result = extract_percentages_from_bunched_cell(
            "10.0 20.0 30.0 40.0", max_count=2
        )
        assert result == [10.0, 20.0]

    def test_multiline_uses_first_line(self) -> None:
        """멀티라인에서 첫 줄만 사용."""
        text = "46.3 13.9 9.8\n49.4 10.9 7.2"
        result = extract_percentages_from_bunched_cell(text)
        assert result == [46.3, 13.9, 9.8]

    def test_integer_tokens(self) -> None:
        """정수도 float으로 변환."""
        result = extract_percentages_from_bunched_cell("46 14 10")
        assert result == [46.0, 14.0, 10.0]

    def test_single_value(self) -> None:
        result = extract_percentages_from_bunched_cell("100.0")
        assert result == [100.0]


# ─── extract_sample_count ────────────────────────────────────────────────────


class TestExtractSampleCount:
    """사례수(N) 추출 테스트."""

    def test_parenthesized_with_comma(self) -> None:
        assert extract_sample_count("(1,007)") == 1007

    def test_parenthesized_without_comma(self) -> None:
        assert extract_sample_count("(1007)") == 1007

    def test_plain_number(self) -> None:
        assert extract_sample_count("1007") == 1007

    def test_plain_with_comma(self) -> None:
        assert extract_sample_count("1,007") == 1007

    def test_empty(self) -> None:
        assert extract_sample_count("") is None

    def test_none_input(self) -> None:
        assert extract_sample_count(None) is None  # type: ignore[arg-type]

    def test_non_numeric(self) -> None:
        assert extract_sample_count("abc") is None

    def test_embedded_in_text(self) -> None:
        assert extract_sample_count("사례수 (500) 명") == 500


# ─── extract_options_from_row ────────────────────────────────────────────────


class TestExtractOptionsFromRow:
    """선택지 추출 테스트."""

    def test_basic(self) -> None:
        row = ["구분", None, "사례수", None, "더불어\n민주당", "국민\n의힘", "조국\n혁신당"]
        result = extract_options_from_row(row, start_col=4)
        assert result == ["더불어 민주당", "국민 의힘", "조국 혁신당"]

    def test_skips_none_and_empty(self) -> None:
        row = ["구분", None, None, "옵션1", None, "옵션2"]
        result = extract_options_from_row(row, start_col=2)
        assert result == ["옵션1", "옵션2"]

    def test_skips_none_string(self) -> None:
        row = ["a", "none", "None", "옵션1"]
        result = extract_options_from_row(row, start_col=0)
        assert result == ["a", "옵션1"]

    def test_end_col(self) -> None:
        row = ["a", "b", "c", "d"]
        result = extract_options_from_row(row, start_col=0, end_col=2)
        assert result == ["a", "b"]

    def test_skip_patterns(self) -> None:
        row = ["옵션1", "(합)", "옵션2", "합계"]
        pats = [re.compile(r"\(합\)"), re.compile(r"^합계$")]
        result = extract_options_from_row(row, start_col=0, skip_patterns=pats)
        assert result == ["옵션1", "옵션2"]

    def test_no_normalize(self) -> None:
        row = ["더불어\n민주당"]
        result = extract_options_from_row(row, start_col=0, normalize_whitespace=False)
        assert result == ["더불어\n민주당"]


# ─── filter_summary_columns ──────────────────────────────────────────────────


class TestFilterSummaryColumns:
    """요약 컬럼 필터링 테스트."""

    def test_removes_hap(self) -> None:
        opts = ["민주당", "(합)", "국민의힘"]
        pcts = [50.0, 80.0, 30.0]
        fo, fp = filter_summary_columns(opts, pcts)
        assert fo == ["민주당", "국민의힘"]
        assert fp == [50.0, 30.0]

    def test_removes_hapgye(self) -> None:
        opts = ["민주당", "합계"]
        pcts = [50.0, 100.0]
        fo, fp = filter_summary_columns(opts, pcts)
        assert fo == ["민주당"]
        assert fp == [50.0]

    def test_removes_t1_b2(self) -> None:
        opts = ["옵션1", "T1", "옵션2", "B2"]
        pcts = [10.0, 40.0, 20.0, 30.0]
        fo, fp = filter_summary_columns(opts, pcts)
        assert fo == ["옵션1", "옵션2"]
        assert fp == [10.0, 20.0]

    def test_removes_circled_composite(self) -> None:
        opts = ["옵션1", "①+②", "옵션2"]
        pcts = [30.0, 60.0, 40.0]
        fo, fp = filter_summary_columns(opts, pcts)
        assert fo == ["옵션1", "옵션2"]
        assert fp == [30.0, 40.0]

    def test_removes_bracket_subtotal(self) -> None:
        opts = ["찬성", "【소계】", "반대"]
        pcts = [40.0, 60.0, 30.0]
        fo, fp = filter_summary_columns(opts, pcts)
        assert fo == ["찬성", "반대"]
        assert fp == [40.0, 30.0]

    def test_keeps_normal(self) -> None:
        opts = ["민주당", "국민의힘", "기타"]
        pcts = [50.0, 30.0, 20.0]
        fo, fp = filter_summary_columns(opts, pcts)
        assert fo == opts
        assert fp == pcts

    def test_mismatched_length_passthrough(self) -> None:
        """길이 불일치 시 원본 그대로 반환."""
        opts = ["a", "b"]
        pcts = [1.0, 2.0, 3.0]
        fo, fp = filter_summary_columns(opts, pcts)
        assert fo == opts
        assert fp == pcts

    def test_removes_parenthesized_sum(self) -> None:
        opts = ["옵션1", "(1+2)", "옵션2"]
        pcts = [30.0, 60.0, 40.0]
        fo, fp = filter_summary_columns(opts, pcts)
        assert fo == ["옵션1", "옵션2"]
        assert fp == [30.0, 40.0]
