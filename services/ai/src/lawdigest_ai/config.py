from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_USE_HTTPS = os.getenv("QDRANT_USE_HTTPS", "false").lower() in ("true", "1", "yes")


def get_openai_api_key() -> str:
    key = os.getenv("OPENAI_API_KEY") or os.getenv("APIKEY_OPENAI")
    if not key:
        raise ValueError("OPENAI_API_KEY 또는 APIKEY_OPENAI 환경변수가 설정되어야 합니다.")
    return key
