import pytest
from unittest.mock import MagicMock, patch


def test_vector_store_search_returns_list(monkeypatch):
    monkeypatch.setenv("QDRANT_HOST", "localhost")
    from lawdigest_ai.rag.vector_store import VectorStore
    with patch("lawdigest_ai.rag.vector_store.QdrantClient") as MockClient:
        instance = MockClient.return_value
        instance.search.return_value = []
        store = VectorStore()
        results = store.search(collection_name="bills", query_vector=[0.1]*10, limit=5)
    assert isinstance(results, list)


def test_vector_store_search_returns_empty_when_client_is_none(monkeypatch):
    """Qdrant 클라이언트가 None일 때 search()는 빈 리스트를 반환해야 한다."""
    monkeypatch.setenv("QDRANT_HOST", "localhost")
    from lawdigest_ai.rag.vector_store import VectorStore
    with patch("lawdigest_ai.rag.vector_store.QdrantClient") as MockClient:
        MockClient.side_effect = Exception("connection failed")
        store = VectorStore()
    results = store.search(collection_name="bills", query_vector=[0.1]*10)
    assert results == []


def test_vector_store_upsert_skips_when_client_is_none(monkeypatch):
    """Qdrant 클라이언트가 None일 때 upsert()는 예외 없이 early return해야 한다."""
    monkeypatch.setenv("QDRANT_HOST", "localhost")
    from lawdigest_ai.rag.vector_store import VectorStore
    with patch("lawdigest_ai.rag.vector_store.QdrantClient") as MockClient:
        MockClient.side_effect = Exception("connection failed")
        store = VectorStore()
    # 예외가 발생하지 않아야 함
    store.upsert(collection_name="bills", points=[])
