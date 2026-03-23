from __future__ import annotations

from typing import List, Optional
from openai import OpenAI
from lawdigest_ai import config


class EmbeddingGenerator:
    """OpenAI 또는 HuggingFace 임베딩 모델로 텍스트 벡터를 생성합니다."""

    def __init__(self, model_type: str = "openai", model_name: Optional[str] = None):
        self.model_type = model_type
        self.client = None
        self.huggingface_model = None

        if model_type == "openai":
            try:
                self.client = OpenAI(api_key=config.get_openai_api_key())
            except Exception as e:
                print(f"OpenAI 클라이언트 초기화 실패: {e}")
        elif model_type == "huggingface":
            if not model_name:
                raise ValueError("HuggingFace 모델을 사용하려면 model_name을 지정해야 합니다.")
            try:
                from sentence_transformers import SentenceTransformer
                self.huggingface_model = SentenceTransformer(model_name)
            except Exception as e:
                print(f"HuggingFace 모델 로드 실패: {e}")

    def generate(self, text: str) -> Optional[List[float]]:
        """텍스트에 대한 임베딩 벡터를 반환합니다."""
        if not text or not isinstance(text, str):
            return None

        if self.model_type == "openai":
            if not self.client:
                return None
            try:
                response = self.client.embeddings.create(
                    input=[text.replace("\n", " ")],
                    model=config.EMBEDDING_MODEL,
                )
                return response.data[0].embedding
            except Exception as e:
                print(f"OpenAI 임베딩 생성 실패: {e}")
                return None

        elif self.model_type == "huggingface":
            if not self.huggingface_model:
                return None
            try:
                return self.huggingface_model.encode(text).tolist()
            except Exception as e:
                print(f"HuggingFace 임베딩 생성 실패: {e}")
                return None
        return None
