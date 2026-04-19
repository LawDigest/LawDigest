import pytest
from typing import get_type_hints


def test_get_batch_provider_returns_openai_batch_stub():
    from lawdigest_ai.processor.providers.router import get_batch_provider
    from lawdigest_ai.processor.providers.openai_batch import OpenAIBatchProvider
    from lawdigest_ai.processor.providers.types import BatchProviderBase

    provider = get_batch_provider("openai")

    assert isinstance(provider, OpenAIBatchProvider)
    assert isinstance(provider, BatchProviderBase)
    assert provider.build_request_rows([], model="gpt-4o-mini") == []


def test_get_batch_provider_accepts_enum_input():
    from lawdigest_ai.processor.providers.router import get_batch_provider
    from lawdigest_ai.processor.providers.gemini_batch import GeminiBatchProvider
    from lawdigest_ai.processor.providers.types import BatchProviderBase, ProviderName

    provider = get_batch_provider(ProviderName.GEMINI)

    assert isinstance(provider, GeminiBatchProvider)
    assert isinstance(provider, BatchProviderBase)


def test_get_instant_provider_returns_gemini_instant_stub():
    from lawdigest_ai.processor.providers.router import get_instant_provider
    from lawdigest_ai.processor.providers.types import GeminiInstantProvider, InstantProviderBase

    provider = get_instant_provider("gemini")

    assert isinstance(provider, GeminiInstantProvider)
    assert isinstance(provider, InstantProviderBase)


def test_get_instant_provider_accepts_enum_input():
    from lawdigest_ai.processor.providers.router import get_instant_provider
    from lawdigest_ai.processor.providers.types import InstantProviderBase, OpenAIInstantProvider, ProviderName

    provider = get_instant_provider(ProviderName.OPENAI)

    assert isinstance(provider, OpenAIInstantProvider)
    assert isinstance(provider, InstantProviderBase)


def test_provider_router_exposes_clear_return_contract():
    from lawdigest_ai.processor.providers.router import get_batch_provider, get_instant_provider
    from lawdigest_ai.processor.providers.types import BatchProviderBase, InstantProviderBase

    assert get_type_hints(get_batch_provider)["return"] is BatchProviderBase
    assert get_type_hints(get_instant_provider)["return"] is InstantProviderBase


def test_provider_router_rejects_invalid_provider():
    from lawdigest_ai.processor.providers.router import get_batch_provider, get_instant_provider

    with pytest.raises(ValueError, match="지원하지 않는 provider"):
        get_batch_provider("claude")

    with pytest.raises(ValueError, match="지원하지 않는 provider"):
        get_instant_provider("claude")
