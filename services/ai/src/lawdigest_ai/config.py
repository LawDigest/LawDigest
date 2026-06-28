from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

_AIRFLOW_DOTENV_PATH = os.getenv("AIRFLOW_DOTENV_PATH")
_DEFAULT_AIRFLOW_DOTENV_PATH = Path(__file__).resolve().parents[4] / "services" / "data" / ".env"
load_dotenv(
    dotenv_path=_AIRFLOW_DOTENV_PATH
    if _AIRFLOW_DOTENV_PATH
    else str(_DEFAULT_AIRFLOW_DOTENV_PATH),
)

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_USE_HTTPS = os.getenv("QDRANT_USE_HTTPS", "false").lower() in ("true", "1", "yes")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
GEMINI_BATCH_MODEL = os.getenv("GEMINI_BATCH_MODEL", GEMINI_MODEL)
GEMINI_INSTANT_MODEL = os.getenv("GEMINI_INSTANT_MODEL", GEMINI_MODEL)
GEMINI_CLI_BIN = os.getenv("GEMINI_CLI_BIN", "gemini")
GEMINI_CLI_MODEL = os.getenv("GEMINI_CLI_MODEL", GEMINI_MODEL)
GEMINI_CLI_TIMEOUT_SECONDS = int(os.getenv("GEMINI_CLI_TIMEOUT_SECONDS", "120"))
GEMINI_CLI_APPROVAL_MODE = os.getenv("GEMINI_CLI_APPROVAL_MODE", "yolo")
GEMINI_CLI_HOME = os.getenv("GEMINI_CLI_HOME")
GEMINI_CLI_WORKDIR = os.getenv("GEMINI_CLI_WORKDIR", "/tmp")
CODEX_CLI_BIN = os.getenv("CODEX_CLI_BIN", "codex")
CODEX_CLI_MODEL = os.getenv("CODEX_CLI_MODEL", "gpt-5.4-mini")
CODEX_CLI_TIMEOUT_SECONDS = int(os.getenv("CODEX_CLI_TIMEOUT_SECONDS", "120"))
CODEX_CLI_HOME = os.getenv("CODEX_CLI_HOME")
CODEX_CLI_WORKDIR = os.getenv("CODEX_CLI_WORKDIR", "/tmp")
CLAUDE_CLI_BIN = os.getenv("CLAUDE_CLI_BIN", "claude")
CLAUDE_CLI_MODEL = os.getenv("CLAUDE_CLI_MODEL", "")
CLAUDE_CLI_TIMEOUT_SECONDS = int(os.getenv("CLAUDE_CLI_TIMEOUT_SECONDS", "120"))
CLAUDE_CLI_HOME = os.getenv("CLAUDE_CLI_HOME")
CLAUDE_CLI_WORKDIR = os.getenv("CLAUDE_CLI_WORKDIR", "/tmp")
LANGFUSE_ENABLED = os.getenv("LANGFUSE_ENABLED", "false").lower() not in {"0", "false", "no", "off"}
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://langfuse.lawdigest.cloud")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_DEBUG = os.getenv("LANGFUSE_DEBUG", "false").lower() in {"1", "true", "yes", "on"}


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
