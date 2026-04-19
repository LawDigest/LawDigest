from __future__ import annotations

from typing import Literal

from lawdigest_ai.processor.providers.types import (
    GeminiBatchProvider,
    GeminiInstantProvider,
    OpenAIBatchProvider,
    OpenAIInstantProvider,
    ProviderName,
)

ProviderKey = Literal["openai", "gemini"]


def _normalize_provider_name(provider: ProviderKey | ProviderName) -> ProviderName:
    if isinstance(provider, ProviderName):
        return provider
    try:
        return ProviderName(provider)
    except ValueError as exc:
        raise ValueError(f"지원하지 않는 provider: {provider}") from exc


def get_batch_provider(provider: ProviderKey | ProviderName):
    provider_name = _normalize_provider_name(provider)
    if provider_name is ProviderName.OPENAI:
        return OpenAIBatchProvider()
    if provider_name is ProviderName.GEMINI:
        return GeminiBatchProvider()
    raise ValueError(f"지원하지 않는 provider: {provider}")


def get_instant_provider(provider: ProviderKey | ProviderName):
    provider_name = _normalize_provider_name(provider)
    if provider_name is ProviderName.OPENAI:
        return OpenAIInstantProvider()
    if provider_name is ProviderName.GEMINI:
        return GeminiInstantProvider()
    raise ValueError(f"지원하지 않는 provider: {provider}")
