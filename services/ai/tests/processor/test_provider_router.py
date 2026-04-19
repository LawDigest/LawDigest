import pytest


def test_get_batch_provider_returns_openai_batch_stub():
    from lawdigest_ai.processor.providers.router import get_batch_provider
    from lawdigest_ai.processor.providers.types import OpenAIBatchProvider

    provider = get_batch_provider("openai")

    assert isinstance(provider, OpenAIBatchProvider)


def test_get_batch_provider_accepts_enum_input():
    from lawdigest_ai.processor.providers.router import get_batch_provider
    from lawdigest_ai.processor.providers.types import GeminiBatchProvider, ProviderName

    provider = get_batch_provider(ProviderName.GEMINI)

    assert isinstance(provider, GeminiBatchProvider)


def test_get_instant_provider_returns_gemini_instant_stub():
    from lawdigest_ai.processor.providers.router import get_instant_provider
    from lawdigest_ai.processor.providers.types import GeminiInstantProvider

    provider = get_instant_provider("gemini")

    assert isinstance(provider, GeminiInstantProvider)


def test_get_instant_provider_accepts_enum_input():
    from lawdigest_ai.processor.providers.router import get_instant_provider
    from lawdigest_ai.processor.providers.types import OpenAIInstantProvider, ProviderName

    provider = get_instant_provider(ProviderName.OPENAI)

    assert isinstance(provider, OpenAIInstantProvider)


def test_provider_router_rejects_invalid_provider():
    from lawdigest_ai.processor.providers.router import get_batch_provider, get_instant_provider

    with pytest.raises(ValueError, match="지원하지 않는 provider"):
        get_batch_provider("claude")

    with pytest.raises(ValueError, match="지원하지 않는 provider"):
        get_instant_provider("claude")
