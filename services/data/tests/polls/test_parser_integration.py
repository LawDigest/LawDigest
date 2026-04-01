"""파서 통합 테스트 – 사전 생성된 픽스처 JSON을 로드하여 속성 검증을 수행한다.

PDF를 직접 파싱하지 않으므로 실행이 빠르다.
픽스처 생성: python scripts/generate_parser_fixtures.py

실행:
    pytest tests/polls/test_parser_integration.py -v
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from lawdigest_data_pipeline.polls.parser import QuestionResult
from lawdigest_data_pipeline.polls.validation import validate_parse_results

# ── 경로 상수 ─────────────────────────────────────────────────────────────────

_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"

# ── 픽스처 로드 헬퍼 ──────────────────────────────────────────────────────────

def _load_fixture(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _dict_to_question_result(d: dict[str, Any]) -> QuestionResult:
    return QuestionResult(
        question_number=d["question_number"],
        question_title=d["question_title"],
        question_text=d.get("question_text", ""),
        response_options=d["response_options"],
        overall_n_completed=d.get("overall_n_completed"),
        overall_n_weighted=d.get("overall_n_weighted"),
        overall_percentages=d["overall_percentages"],
    )


# ── 테스트 파라미터 수집 ──────────────────────────────────────────────────────

def _collect_cases() -> list[tuple[str, str, list[QuestionResult]]]:
    """fixtures/ 디렉터리의 모든 JSON 파일을 로드하여 (pollster, pdf_filename, results) 반환."""
    cases = []
    for json_path in sorted(_FIXTURE_DIR.glob("*.json")):
        data = _load_fixture(json_path)
        results = [_dict_to_question_result(q) for q in data["questions"]]
        cases.append((data["pollster"], data["pdf_filename"], results))
    return cases


_CASES = _collect_cases()


def _case_id(case: tuple) -> str:
    pollster, fname, _ = case
    return f"{pollster}|{Path(fname).stem[:30]}"


# ── 통합 테스트 ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("pollster,fname,results", _CASES, ids=[_case_id(c) for c in _CASES])
def test_fixture_has_questions(
    pollster: str,
    fname: str,
    results: list[QuestionResult],
) -> None:
    """픽스처에 최소 1개 이상의 질문이 존재하는지 확인한다."""
    assert len(results) >= 1, (
        f"질문이 없음: {pollster} / {fname}"
    )


@pytest.mark.parametrize("pollster,fname,results", _CASES, ids=[_case_id(c) for c in _CASES])
def test_fixture_results_pass_property_validation(
    pollster: str,
    fname: str,
    results: list[QuestionResult],
) -> None:
    """픽스처의 모든 QuestionResult가 속성 검증을 통과하는지 확인한다.

    검증 항목:
    - question_number >= 1
    - question_title 비어있지 않음
    - response_options, overall_percentages 비어있지 않음
    - len(options) == len(percentages)
    - 각 percentage: 0 ≤ p ≤ 100
    - sum(percentages) ∈ [75, 115]  (반올림·가중 오차 허용)
    - overall_n_weighted >= 50
    """
    errors = validate_parse_results(results)

    assert not errors, (
        f"속성 검증 실패 ({pollster} / {fname}):\n"
        + "\n".join(f"  [{q}] {msgs}" for q, msgs in errors.items())
    )
