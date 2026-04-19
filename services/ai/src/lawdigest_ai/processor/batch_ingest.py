from __future__ import annotations

from typing import Any, Dict

from lawdigest_ai.db import get_db_connection
from lawdigest_ai.processor.provider_batch_service import (
    IngestProvider,
    ingest_batch_results_for_provider,
)


def ingest_batch_results(
    max_jobs: int = 10,
    mode: str = "dry_run",
    provider: IngestProvider = "all",
) -> Dict[str, Any]:
    """완료된 provider-aware Batch 작업의 결과를 수집하여 DB에 적재합니다.

    Args:
        max_jobs: 한 번에 처리할 최대 작업 수
        mode: 'dry_run' | 'test' | 'prod'
        provider: 'openai' | 'gemini' | 'all'
    """
    conn = get_db_connection(mode=mode if mode == "prod" else "test")
    try:
        return ingest_batch_results_for_provider(
            conn=conn,
            max_jobs=max_jobs,
            mode=mode,
            provider=provider,
        )
    finally:
        conn.close()
