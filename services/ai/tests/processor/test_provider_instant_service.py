from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from lawdigest_ai.config import GEMINI_INSTANT_MODEL, SUMMARY_STRUCTURED_MODEL
from lawdigest_ai.processor.providers.types import InstantProviderResult


def test_summarize_single_bill_routes_provider_with_default_model():
    from lawdigest_ai.processor.provider_instant_service import summarize_single_bill_with_provider

    provider = MagicMock()
    provider.summarize_bill.return_value = InstantProviderResult(
        bill_id="B001",
        brief_summary="요약",
        gpt_summary="상세",
        summary_tags='["a","b","c","d","e"]',
        error=None,
    )

    with patch(
        "lawdigest_ai.processor.provider_instant_service.get_instant_provider",
        return_value=provider,
    ):
        result = summarize_single_bill_with_provider(
            {"bill_id": "B001", "summary": "원문 내용"},
            provider="gemini",
            model=None,
        )

    provider.summarize_bill.assert_called_once_with(
        {"bill_id": "B001", "summary": "원문 내용"},
        model=GEMINI_INSTANT_MODEL,
    )
    assert result["bill_id"] == "B001"
    assert result["brief_summary"] == "요약"


def test_summarize_single_bill_raises_when_provider_returns_error():
    from lawdigest_ai.processor.provider_instant_service import summarize_single_bill_with_provider

    provider = MagicMock()
    provider.summarize_bill.return_value = InstantProviderResult(
        bill_id="B001",
        brief_summary=None,
        gpt_summary=None,
        summary_tags=None,
        error="요약 실패",
    )

    with (
        patch(
            "lawdigest_ai.processor.provider_instant_service.get_instant_provider",
            return_value=provider,
        ),
        pytest.raises(RuntimeError, match="요약 실패"),
    ):
        summarize_single_bill_with_provider(
            {"bill_id": "B001", "summary": "원문 내용"},
            provider="openai",
        )


def test_summarize_bills_routes_provider_with_openai_default_model():
    from lawdigest_ai.processor.provider_instant_service import summarize_bills_with_provider

    provider = MagicMock()
    provider.summarize_bills.return_value = [
        InstantProviderResult(
            bill_id="B001",
            brief_summary="요약1",
            gpt_summary="상세1",
            summary_tags='["a","b","c","d","e"]',
            error=None,
        ),
        InstantProviderResult(
            bill_id="B002",
            brief_summary=None,
            gpt_summary=None,
            summary_tags=None,
            error="응답 파싱 실패",
        ),
    ]

    bills = [
        {"bill_id": "B001", "summary": "원문1"},
        {"bill_id": "B002", "summary": "원문2"},
    ]

    with patch(
        "lawdigest_ai.processor.provider_instant_service.get_instant_provider",
        return_value=provider,
    ):
        result = summarize_bills_with_provider(bills, provider="openai", model=None)

    provider.summarize_bills.assert_called_once_with(bills, model=SUMMARY_STRUCTURED_MODEL)
    assert result[0]["brief_summary"] == "요약1"
    assert result[1]["error"] == "응답 파싱 실패"
