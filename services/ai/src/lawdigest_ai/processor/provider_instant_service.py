from __future__ import annotations

from typing import Any, Dict, List, Literal

from lawdigest_ai.config import GEMINI_INSTANT_MODEL, SUMMARY_STRUCTURED_MODEL
from lawdigest_ai.processor.providers import get_instant_provider
from lawdigest_ai.processor.providers.types import InstantProviderResult

InstantProviderName = Literal["openai", "gemini"]

DEFAULT_INSTANT_MODELS: dict[InstantProviderName, str] = {
    "openai": SUMMARY_STRUCTURED_MODEL,
    "gemini": GEMINI_INSTANT_MODEL,
}


def resolve_instant_model(provider: InstantProviderName, model: str | None) -> str:
    if model:
        return model
    return DEFAULT_INSTANT_MODELS[provider]


def _result_to_dict(result: InstantProviderResult) -> Dict[str, Any]:
    return {
        "bill_id": result.bill_id,
        "brief_summary": result.brief_summary,
        "gpt_summary": result.gpt_summary,
        "summary_tags": result.summary_tags,
        "error": result.error,
    }


def summarize_single_bill_with_provider(
    bill_data: Dict[str, Any],
    *,
    provider: InstantProviderName = "openai",
    model: str | None = None,
) -> Dict[str, Any]:
    resolved_model = resolve_instant_model(provider, model)
    provider_instance = get_instant_provider(provider)
    result = provider_instance.summarize_bill(bill_data, model=resolved_model)
    if result.error:
        raise RuntimeError(result.error)
    return _result_to_dict(result)


def summarize_bills_with_provider(
    bills: List[Dict[str, Any]],
    *,
    provider: InstantProviderName = "openai",
    model: str | None = None,
) -> List[Dict[str, Any]]:
    resolved_model = resolve_instant_model(provider, model)
    provider_instance = get_instant_provider(provider)
    results = provider_instance.summarize_bills(bills, model=resolved_model)
    return [_result_to_dict(result) for result in results]
