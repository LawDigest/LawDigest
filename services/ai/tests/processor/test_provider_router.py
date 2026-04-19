def test_get_batch_provider_routes_openai():
    from lawdigest_ai.processor.providers.router import get_batch_provider
    from lawdigest_ai.processor.providers.types import ProviderName

    provider = get_batch_provider("openai")

    assert provider.provider_name == ProviderName.OPENAI


def test_get_instant_provider_routes_gemini():
    from lawdigest_ai.processor.providers.router import get_instant_provider
    from lawdigest_ai.processor.providers.types import ProviderName

    provider = get_instant_provider("gemini")

    assert provider.provider_name == ProviderName.GEMINI
