"""파서 결과 속성 검증 단위 테스트 (PDF 파일 불필요)."""
from __future__ import annotations

from lawdigest_data.polls.models import QuestionResult
from lawdigest_data.polls.validation import (
    quality_screen_question_result,
    validate_parse_results,
    validate_question_result,
)


# ── 헬퍼 ──────────────────────────────────────────────────────────────────────

def _make_q(**kwargs) -> QuestionResult:
    """기본값이 모두 유효한 QuestionResult를 생성한다."""
    defaults: dict = {
        "question_number": 1,
        "question_title": "정당 지지도",
        "question_text": "",
        "response_options": ["더불어민주당", "국민의힘", "모름"],
        "overall_n_completed": 1000,
        "overall_n_weighted": 1000,
        "overall_percentages": [50.0, 40.0, 10.0],
    }
    defaults.update(kwargs)
    return QuestionResult(**defaults)


def _has_error_containing(errors, keyword: str) -> bool:
    return any(keyword in e.message for e in errors)


# ── 정상 케이스 ───────────────────────────────────────────────────────────────

class TestValidResult:
    def test_valid_result_has_no_errors(self):
        assert validate_question_result(_make_q()) == []

    def test_none_n_values_are_allowed(self):
        """일부 파서는 N값을 추출하지 못할 수 있어 None 허용."""
        r = _make_q(overall_n_completed=None, overall_n_weighted=None)
        assert validate_question_result(r) == []

    def test_sum_exactly_100(self):
        r = _make_q(
            response_options=["A", "B"],
            overall_percentages=[60.0, 40.0],
        )
        assert validate_question_result(r) == []

    def test_sum_within_tolerance_high(self):
        """반올림 오차로 합계가 101% 정도는 허용."""
        r = _make_q(
            response_options=["A", "B", "C"],
            overall_percentages=[34.0, 34.0, 33.0],  # 합 101%
        )
        assert validate_question_result(r) == []

    def test_sum_within_tolerance_low(self):
        """모름/무응답 컬럼 누락으로 합계가 80%여도 허용."""
        r = _make_q(
            response_options=["A", "B"],
            overall_percentages=[50.0, 30.0],  # 합 80%
        )
        assert validate_question_result(r) == []


# ── 질문 번호 ─────────────────────────────────────────────────────────────────

class TestQuestionNumber:
    def test_zero_question_number_is_invalid(self):
        errors = validate_question_result(_make_q(question_number=0))
        assert _has_error_containing(errors, "번호")

    def test_negative_question_number_is_invalid(self):
        errors = validate_question_result(_make_q(question_number=-1))
        assert _has_error_containing(errors, "번호")

    def test_question_number_one_is_valid(self):
        assert validate_question_result(_make_q(question_number=1)) == []


# ── 질문 제목 ─────────────────────────────────────────────────────────────────

class TestQuestionTitle:
    def test_empty_title_is_invalid(self):
        errors = validate_question_result(_make_q(question_title=""))
        assert _has_error_containing(errors, "제목")

    def test_whitespace_only_title_is_invalid(self):
        errors = validate_question_result(_make_q(question_title="   "))
        assert _has_error_containing(errors, "제목")


class TestQualityScreening:
    def test_rejects_placeholder_question_title(self):
        errors = quality_screen_question_result(_make_q(question_title="Q7"))
        assert _has_error_containing(errors, "placeholder")

    def test_rejects_placeholder_options(self):
        errors = quality_screen_question_result(
            _make_q(response_options=["선택지1", "선택지2"], overall_percentages=[38.0, 27.0])
        )
        assert _has_error_containing(errors, "placeholder")

    def test_rejects_merged_party_labels(self):
        errors = quality_screen_question_result(
            _make_q(
                response_options=["민주당국민의힘", "혁신당개혁신당진보당", "잘 모르겠다"],
                overall_percentages=[39.9, 2.0, 17.5],
            )
        )
        assert _has_error_containing(errors, "병합")

    def test_rejects_mojibake_text(self):
        errors = quality_screen_question_result(
            _make_q(
                question_title="먚鰃믅믅鱮 (1)",
                response_options=["꾍랹 긁묁鰃", "긁륝 증", "롽 먚鰃"],
                overall_percentages=[56.1, 29.3, 3.1],
            )
        )
        assert _has_error_containing(errors, "문자 깨짐")

    def test_allows_clean_question_result(self):
        assert quality_screen_question_result(_make_q()) == []


# ── 선택지 / 비율 ─────────────────────────────────────────────────────────────

class TestOptionsAndPercentages:
    def test_empty_options_is_invalid(self):
        errors = validate_question_result(
            _make_q(response_options=[], overall_percentages=[])
        )
        assert _has_error_containing(errors, "선택지")

    def test_empty_percentages_is_invalid(self):
        errors = validate_question_result(
            _make_q(response_options=["A"], overall_percentages=[])
        )
        assert _has_error_containing(errors, "비율")

    def test_length_mismatch_is_invalid(self):
        errors = validate_question_result(
            _make_q(
                response_options=["A", "B"],
                overall_percentages=[50.0, 40.0, 10.0],
            )
        )
        assert _has_error_containing(errors, "불일치")

    def test_single_option_100pct_is_valid(self):
        r = _make_q(
            response_options=["예"],
            overall_percentages=[100.0],
        )
        assert validate_question_result(r) == []


# ── 개별 비율 범위 ────────────────────────────────────────────────────────────

class TestPercentageValues:
    def test_negative_percentage_is_invalid(self):
        errors = validate_question_result(
            _make_q(
                response_options=["A", "B", "C"],
                overall_percentages=[-5.0, 65.0, 40.0],
            )
        )
        assert _has_error_containing(errors, "음수")

    def test_over_100_percentage_is_invalid(self):
        errors = validate_question_result(
            _make_q(
                response_options=["A"],
                overall_percentages=[101.0],
            )
        )
        assert _has_error_containing(errors, "초과")

    def test_zero_percentage_is_valid(self):
        r = _make_q(
            response_options=["A", "B", "C"],
            overall_percentages=[0.0, 50.0, 50.0],
        )
        assert validate_question_result(r) == []


# ── 비율 합계 ─────────────────────────────────────────────────────────────────

class TestPercentageSum:
    def test_sum_too_low_is_invalid(self):
        """합계가 75% 미만이면 오류."""
        errors = validate_question_result(
            _make_q(
                response_options=["A", "B"],
                overall_percentages=[10.0, 20.0],  # 합 30%
            )
        )
        assert _has_error_containing(errors, "합계")

    def test_sum_too_high_is_invalid(self):
        """합계가 115% 초과이면 오류 (소계 컬럼이 섞여든 경우 등)."""
        errors = validate_question_result(
            _make_q(
                response_options=["A", "B", "소계"],
                overall_percentages=[60.0, 40.0, 100.0],  # 합 200%
            )
        )
        assert _has_error_containing(errors, "합계")

    def test_sum_at_lower_boundary_is_valid(self):
        r = _make_q(
            response_options=["A", "B"],
            overall_percentages=[50.0, 25.0],  # 합 75%
        )
        assert validate_question_result(r) == []

    def test_sum_at_upper_boundary_is_valid(self):
        r = _make_q(
            response_options=["A", "B"],
            overall_percentages=[75.0, 40.0],  # 합 115%
        )
        assert validate_question_result(r) == []


# ── 표본 수 ───────────────────────────────────────────────────────────────────

class TestSampleSize:
    def test_sample_size_too_small_is_invalid(self):
        errors = validate_question_result(_make_q(overall_n_completed=10))
        assert _has_error_containing(errors, "표본")

    def test_sample_size_50_is_valid(self):
        assert validate_question_result(_make_q(overall_n_completed=50)) == []

    def test_large_sample_size_is_valid(self):
        assert validate_question_result(_make_q(overall_n_completed=5000)) == []


# ── validate_parse_results ────────────────────────────────────────────────────

class TestValidateParseResults:
    def test_empty_list_returns_empty_error(self):
        result = validate_parse_results([])
        assert "_empty" in result

    def test_valid_results_return_empty_dict(self):
        results = [_make_q(question_number=i) for i in range(1, 4)]
        assert validate_parse_results(results) == {}

    def test_invalid_result_key_includes_question_number_and_title(self):
        results = [_make_q(question_number=3, question_title="정당지지도", overall_percentages=[10.0])]
        errors = validate_parse_results(results)
        assert any("Q3" in k for k in errors)

    def test_multiple_invalid_results_all_reported(self):
        results = [
            _make_q(question_number=1, question_title=""),
            _make_q(question_number=2, overall_percentages=[5.0]),  # 합 5%
        ]
        errors = validate_parse_results(results)
        assert len(errors) == 2
