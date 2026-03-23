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


def test_embedding_generator_returns_none_for_none_client(monkeypatch):
    """OpenAI 클라이언트가 None일 때 generate()는 None을 반환해야 한다."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    from lawdigest_ai.rag.embedding import EmbeddingGenerator
    with patch("lawdigest_ai.rag.embedding.OpenAI") as MockOpenAI:
        MockOpenAI.side_effect = Exception("init failed")
        gen = EmbeddingGenerator(model_type="openai")
    result = gen.generate("some text")
    assert result is None


def test_embedding_generator_openai_returns_vector(monkeypatch):
    """정상적인 OpenAI 응답에서 벡터 리스트를 반환해야 한다."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    from lawdigest_ai.rag.embedding import EmbeddingGenerator
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
    with patch("lawdigest_ai.rag.embedding.OpenAI") as MockOpenAI:
        instance = MockOpenAI.return_value
        instance.embeddings.create.return_value = mock_response
        gen = EmbeddingGenerator(model_type="openai")
        result = gen.generate("테스트 텍스트")
    assert result == [0.1, 0.2, 0.3]
