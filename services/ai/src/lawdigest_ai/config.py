from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_USE_HTTPS = os.getenv("QDRANT_USE_HTTPS", "false").lower() in ("true", "1", "yes")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("APIKEY_GEMINI")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_BATCH_MODEL = os.getenv("GEMINI_BATCH_MODEL", GEMINI_MODEL)
GEMINI_INSTANT_MODEL = os.getenv("GEMINI_INSTANT_MODEL", GEMINI_MODEL)
GEMINI_CLI_BIN = os.getenv("GEMINI_CLI_BIN", "gemini")
GEMINI_CLI_MODEL = os.getenv("GEMINI_CLI_MODEL", os.getenv("GEMINI_MODEL", "auto-gemini-3"))
GEMINI_CLI_TIMEOUT_SECONDS = int(os.getenv("GEMINI_CLI_TIMEOUT_SECONDS", "120"))
GEMINI_CLI_APPROVAL_MODE = os.getenv("GEMINI_CLI_APPROVAL_MODE", "yolo")
GEMINI_CLI_HOME = os.getenv("GEMINI_CLI_HOME")
GEMINI_CLI_WORKDIR = os.getenv("GEMINI_CLI_WORKDIR", "/tmp")


def get_openai_api_key() -> str:
    key = os.getenv("OPENAI_API_KEY") or os.getenv("APIKEY_OPENAI")
    if not key:
        raise ValueError("OPENAI_API_KEY 또는 APIKEY_OPENAI 환경변수가 설정되어야 합니다.")
    return key


def get_gemini_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY") or os.getenv("APIKEY_GEMINI")
    if not key:
        raise ValueError("GEMINI_API_KEY 또는 APIKEY_GEMINI 환경변수가 설정되어야 합니다.")
    return key

SUMMARY_STRUCTURED_MODEL = os.getenv("SUMMARY_STRUCTURED_MODEL", "openai:gpt-4o-mini")
SUMMARY_STRUCTURED_FALLBACK_MODEL = os.getenv("SUMMARY_STRUCTURED_FALLBACK_MODEL", "openai:gpt-4o-mini")
