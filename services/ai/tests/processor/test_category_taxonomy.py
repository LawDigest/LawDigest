import pytest

from lawdigest_ai.processor.category_taxonomy import (
    CATEGORIES,
    CATEGORY_CODES,
    CATEGORY_LABELS,
    UNKNOWN_CODE,
    build_category_prompt_block,
    category_label_to_code,
)
from lawdigest_ai.processor.providers.openai_batch import (
    BatchStructuredSummary,
    _build_prompt_for_bill,
)


def test_taxonomy_has_17_unique_codes_and_labels():
    assert len(CATEGORIES) == 17
    assert len(set(CATEGORY_CODES)) == 17
    assert len(set(CATEGORY_LABELS)) == 17
    assert UNKNOWN_CODE not in CATEGORY_CODES


@pytest.mark.parametrize("category", CATEGORIES)
def test_label_to_code_roundtrip(category):
    assert category_label_to_code(category.label) == category.code


def test_label_to_code_unknown_fallback():
    assert category_label_to_code(None) == UNKNOWN_CODE
    assert category_label_to_code("존재하지않는분야") == UNKNOWN_CODE
    assert category_label_to_code("  경제·세금  ") == "economy"


def test_prompt_block_lists_all_labels_and_priority_rule():
    block = build_category_prompt_block()
    for label in CATEGORY_LABELS:
        assert label in block
    assert "법률 종류" in block  # 법안명 우선 규칙


@pytest.mark.parametrize("category", CATEGORIES)
def test_model_accepts_every_label(category):
    model = BatchStructuredSummary(
        title="요약",
        gpt_summary="상세",
        tags=["a", "b", "c", "d", "e"],
        category=category.label,
    )
    assert model.category == category.label


def test_model_rejects_invalid_category():
    with pytest.raises(Exception):
        BatchStructuredSummary(
            title="요약",
            gpt_summary="상세",
            tags=["a", "b", "c", "d", "e"],
            category="없는분야",
        )


def test_build_prompt_includes_category_section():
    prompt = _build_prompt_for_bill({"bill_id": "B1", "bill_name": "테스트법", "summary": "원문"})
    assert "키는 title, gptSummary, tags, category 네 개만 포함해야 합니다." in prompt
    assert "category는 아래 17개 분야" in prompt
