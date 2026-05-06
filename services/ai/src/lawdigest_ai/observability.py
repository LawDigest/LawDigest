from __future__ import annotations

import atexit
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional

from lawdigest_ai.config import (
    LANGFUSE_DEBUG,
    LANGFUSE_ENABLED,
    LANGFUSE_HOST,
    LANGFUSE_PUBLIC_KEY,
    LANGFUSE_SECRET_KEY,
)

try:
    from langfuse import Langfuse
except Exception:  # pragma: no cover
    Langfuse = None  # type: ignore[assignment]


_LANGFUSE_CLIENT = None
_CLIENT_INIT_ERROR: Optional[str] = None


def _build_client() -> Any:
    global _LANGFUSE_CLIENT, _CLIENT_INIT_ERROR

    if _CLIENT_INIT_ERROR is not None:
        return None

    if not LANGFUSE_ENABLED:
        return None

    if Langfuse is None:
        _CLIENT_INIT_ERROR = "langfuse 패키지가 설치되지 않았습니다."
        return None

    if not LANGFUSE_PUBLIC_KEY or not LANGFUSE_SECRET_KEY:
        _CLIENT_INIT_ERROR = "LANGFUSE_PUBLIC_KEY 또는 LANGFUSE_SECRET_KEY가 설정되지 않았습니다."
        return None

    if _LANGFUSE_CLIENT is not None:
        return _LANGFUSE_CLIENT

    try:
        kwargs: Dict[str, Any] = {
            "public_key": LANGFUSE_PUBLIC_KEY,
            "secret_key": LANGFUSE_SECRET_KEY,
            "debug": LANGFUSE_DEBUG,
        }
        if LANGFUSE_HOST:
            kwargs["host"] = LANGFUSE_HOST
        _LANGFUSE_CLIENT = Langfuse(**kwargs)
        return _LANGFUSE_CLIENT
    except Exception as exc:
        _CLIENT_INIT_ERROR = f"Langfuse client 생성 실패: {exc}"
        return None


def _finalize_client() -> None:
    if _LANGFUSE_CLIENT is None:
        return
    try:
        _LANGFUSE_CLIENT.flush()
        _LANGFUSE_CLIENT.shutdown()
    except Exception:
        pass


atexit.register(_finalize_client)


@contextmanager
def trace_span(
    name: str,
    *,
    input: Any | None = None,
    output: Any | None = None,
    metadata: Dict[str, Any] | None = None,
) -> Iterator[Any | None]:
    client = _build_client()
    if client is None:
        yield None
        return

    with client.start_as_current_span(
        name=name,
        input=input,
        output=output,
        metadata=metadata,
    ) as span:
        try:
            yield span
            if output is None:
                span.update(output=None)
        except Exception as exc:
            try:
                span.update(level="ERROR", status_message=str(exc))
            except Exception:
                pass
            raise


@contextmanager
def trace_generation(
    parent_span: Any,
    *,
    name: str,
    model: str,
    input: Any | None = None,
    output: Any | None = None,
    metadata: Dict[str, Any] | None = None,
) -> Iterator[Any | None]:
    if parent_span is None:
        yield None
        return

    with parent_span.start_as_current_observation(
        name=name,
        as_type="generation",
        model=model,
        input=input,
        output=output,
        metadata=metadata,
    ) as generation:
        try:
            yield generation
            if output is None:
                generation.update(output=None)
        except Exception as exc:
            try:
                generation.update(level="ERROR", status_message=str(exc))
            except Exception:
                pass
            raise
