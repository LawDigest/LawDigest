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
