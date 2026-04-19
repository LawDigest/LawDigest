from __future__ import annotations

from typing import Any, Dict

from lawdigest_ai.db import get_db_connection
from lawdigest_ai.processor.provider_batch_service import (
    SubmitProvider,
    submit_batches,
)


def submit_batch(
    limit: int = 200,
    model: str | None = None,
    mode: str = "dry_run",
    provider: SubmitProvider = "openai",
) -> Dict[str, Any]:
    """미요약 법안을 provider-aware Batch API에 제출합니다.

    Args:
        limit: 한 번에 처리할 최대 법안 수
        model: 사용할 배치 모델명. 비워두면 provider 기본 모델 사용
        mode: 'dry_run' | 'test' | 'prod'
        provider: 'openai' | 'gemini'
    """
    conn = get_db_connection(mode=mode if mode == "prod" else "test")
    try:
        return submit_batches(
            conn=conn,
            limit=limit,
            model=model,
            mode=mode,
            provider=provider,
        )
    finally:
        conn.close()
