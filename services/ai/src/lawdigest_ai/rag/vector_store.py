from __future__ import annotations

from typing import Any, Dict, List, Optional
import qdrant_client
from qdrant_client import QdrantClient
from qdrant_client.http import models
from lawdigest_ai import config


class VectorStore:
    """Qdrant 벡터 DB와의 연결 및 상호작용을 관리합니다."""

    def __init__(self):
        try:
            self.client = QdrantClient(
                host=config.QDRANT_HOST,
                api_key=config.QDRANT_API_KEY,
                port=6333,
                https=config.QDRANT_USE_HTTPS,
            )
        except Exception as e:
            print(f"Qdrant 클라이언트 초기화 실패: {e}")
            self.client = None

    def create_collection(self, collection_name: str, vector_size: int, recreate: bool = False) -> None:
        if not self.client:
            return
        if recreate:
            self.client.recreate_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
            )
            return
        existing = [c.name for c in self.client.get_collections().collections]
        if collection_name not in existing:
            self.client.recreate_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
            )

    def upsert(self, collection_name: str, points: list) -> None:
        if not self.client or not points:
            return
        self.client.upsert(collection_name=collection_name, points=points, wait=True)

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: Optional[float] = None,
    ) -> List[Any]:
        """벡터 유사도 검색을 수행하고 결과를 반환합니다."""
        if not self.client:
            return []
        kwargs: Dict[str, Any] = {
            "collection_name": collection_name,
            "query_vector": query_vector,
            "limit": limit,
        }
        if score_threshold is not None:
            kwargs["score_threshold"] = score_threshold
        return self.client.search(**kwargs)
