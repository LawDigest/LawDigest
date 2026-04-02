"""여론조사 파싱 결과 속성 검증 모듈."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .models import QuestionResult

# 비율 합계 허용 범위 (단일응답 기준)
# - 반올림 오차: ±5%
# - 일부 파서에서 마지막 '모름/무응답' 컬럼 누락 가능성: 추가 -15%
_PCT_SUM_MIN = 75.0
_PCT_SUM_MAX = 115.0

# 개별 비율 허용 범위
_PCT_VALUE_MIN = 0.0
_PCT_VALUE_MAX = 100.0

# 최소 허용 표본 수
_N_MIN = 50


@dataclass(frozen=True)
class ValidationError:
    field: str
    message: str


def validate_question_result(r: QuestionResult) -> List[ValidationError]:
    """단일 QuestionResult의 속성을 검증하고 오류 목록을 반환한다.

    반환된 리스트가 비어있으면 검증 통과.
    """
    errors: List[ValidationError] = []

    # ── 질문 번호 ────────────────────────────────────────────────────────
    if r.question_number < 1:
        errors.append(ValidationError(
            "question_number",
            f"질문 번호 비정상: {r.question_number} (1 이상이어야 함)",
        ))

    # ── 질문 제목 ────────────────────────────────────────────────────────
    if not r.question_title or not r.question_title.strip():
        errors.append(ValidationError("question_title", "질문 제목이 비어있음"))

    # ── 선택지 / 비율 존재 여부 ──────────────────────────────────────────
    if not r.response_options:
        errors.append(ValidationError("response_options", "선택지가 없음"))

    if not r.overall_percentages:
        errors.append(ValidationError("overall_percentages", "전체 비율이 없음"))

    # ── 선택지 수 ↔ 비율 수 일치 ─────────────────────────────────────────
    n_opts = len(r.response_options)
    n_pcts = len(r.overall_percentages)
    if n_opts != n_pcts:
        errors.append(ValidationError(
            "response_options/overall_percentages",
            f"선택지 수({n_opts})와 비율 수({n_pcts}) 불일치",
        ))

    # ── 개별 비율 범위 ────────────────────────────────────────────────────
    for i, p in enumerate(r.overall_percentages):
        if p < _PCT_VALUE_MIN:
            errors.append(ValidationError(
                f"overall_percentages[{i}]",
                f"음수 비율: {p}",
            ))
        elif p > _PCT_VALUE_MAX:
            errors.append(ValidationError(
                f"overall_percentages[{i}]",
                f"100% 초과 비율: {p}",
            ))

    # ── 비율 합계 ─────────────────────────────────────────────────────────
    if r.overall_percentages:
        total = sum(r.overall_percentages)
        if not (_PCT_SUM_MIN <= total <= _PCT_SUM_MAX):
            errors.append(ValidationError(
                "overall_percentages",
                f"비율 합계 비정상: {total:.1f}% (허용 범위: {_PCT_SUM_MIN}~{_PCT_SUM_MAX}%)",
            ))

    # ── 표본 수 ───────────────────────────────────────────────────────────
    if r.overall_n_completed is not None and r.overall_n_completed < _N_MIN:
        errors.append(ValidationError(
            "overall_n_completed",
            f"표본 수가 너무 작음: {r.overall_n_completed} (최소 {_N_MIN})",
        ))

    return errors


def validate_parse_results(
    results: List[QuestionResult],
) -> Dict[str, List[str]]:
    """파싱 결과 목록 전체를 검증하고 질문별 오류 딕셔너리를 반환한다.

    Returns:
        key = "Q{n}_{제목앞20자}", value = 오류 메시지 목록
        오류가 없으면 빈 딕셔너리 반환.
    """
    if not results:
        return {"_empty": ["파싱 결과가 없음 (질문 0건)"]}

    all_errors: Dict[str, List[str]] = {}
    for r in results:
        errs = validate_question_result(r)
        if errs:
            key = f"Q{r.question_number}_{r.question_title[:20]}"
            all_errors[key] = [e.message for e in errs]

    return all_errors
