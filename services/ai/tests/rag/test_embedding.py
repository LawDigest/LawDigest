import pytest
from unittest.mock import patch, MagicMock


def test_embedding_generator_openai_init(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    from lawdigest_ai.rag.embedding import EmbeddingGenerator
    with patch("lawdigest_ai.rag.embedding.OpenAI"):
        gen = EmbeddingGenerator(model_type="openai")
    assert gen.model_type == "openai"


def test_embedding_generator_returns_none_for_empty_text(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    from lawdigest_ai.rag.embedding import EmbeddingGenerator
    with patch("lawdigest_ai.rag.embedding.OpenAI"):
        gen = EmbeddingGenerator(model_type="openai")
    result = gen.generate("")
    assert result is None
