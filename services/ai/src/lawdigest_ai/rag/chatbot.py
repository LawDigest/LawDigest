from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

from openai import OpenAI
from lawdigest_ai import config
from lawdigest_ai.rag.embedding import EmbeddingGenerator
from lawdigest_ai.rag.vector_store import VectorStore

BILL_COLLECTION = os.getenv("QDRANT_BILL_COLLECTION", "bills")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
RAG_MODEL = os.getenv("RAG_MODEL", "gpt-4o-mini")


class LawdigestionChatbot:
    """Qdrant 벡터 검색 + OpenAI LLM을 결합한 법안 RAG 챗봇."""

    def __init__(
        self,
        collection_name: str = BILL_COLLECTION,
        top_k: int = RAG_TOP_K,
        model: str = RAG_MODEL,
    ):
        self.collection_name = collection_name
        self.top_k = top_k
        self.model = model
        self.embedder = EmbeddingGenerator(model_type="openai")
        self.vector_store = VectorStore()
        self.llm = OpenAI(api_key=config.get_openai_api_key())

    def _retrieve(self, query: str) -> List[Dict[str, Any]]:
        """쿼리에 관련된 법안을 벡터 DB에서 검색합니다."""
        vector = self.embedder.generate(query)
        if not vector:
            return []
        results = self.vector_store.search(
            collection_name=self.collection_name,
            query_vector=vector,
            limit=self.top_k,
        )
        return [r.payload for r in results if r.payload]

    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """검색된 법안 문서로 LLM 컨텍스트를 구성합니다."""
        if not documents:
            return "관련 법안 정보를 찾을 수 없습니다."
        lines = []
        for i, doc in enumerate(documents, 1):
            lines.append(
                f"[법안 {i}]\n"
                f"법안명: {doc.get('bill_name', '미상')}\n"
                f"한줄요약: {doc.get('brief_summary', '')}\n"
                f"상세요약: {doc.get('gpt_summary', '')}\n"
            )
        return "\n".join(lines)

    def _call_llm(self, query: str, context: str) -> str:
        """LLM에 쿼리와 컨텍스트를 전달하여 답변을 생성합니다."""
        system_prompt = (
            "당신은 대한민국 법안 전문 AI 어시스턴트입니다. "
            "제공된 법안 정보를 바탕으로 사용자 질문에 명확하고 친절하게 답변하세요. "
            "법안 정보에 없는 내용은 추측하지 마세요."
        )
        user_prompt = f"[참고 법안 정보]\n{context}\n\n[질문]\n{query}"
        try:
            response = self.llm.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.exception(f"LLM 호출 실패: {e}")
            return "죄송합니다. 일시적인 오류가 발생했습니다."

    def answer(self, query: str) -> str:
        """사용자 질문에 대한 RAG 기반 답변을 반환합니다."""
        documents = self._retrieve(query)
        context = self._build_context(documents)
        return self._call_llm(query, context)
