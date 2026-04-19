from pathlib import Path
from unittest.mock import MagicMock

from lawdigest_ai.processor.batch_utils import (
    build_batch_request_rows,
    create_batch_job_with_items,
    ensure_status_tables,
)
from lawdigest_ai.processor.providers.openai_batch import OpenAIBatchProvider


def test_ensure_status_tables_includes_provider_scoped_job_keys():
    conn = MagicMock()
    cursor = MagicMock()
    cursor.__enter__ = MagicMock(return_value=cursor)
    cursor.__exit__ = MagicMock(return_value=False)
    conn.cursor.return_value = cursor

    ensure_status_tables(conn)

    executed_sql = [call.args[0] for call in cursor.execute.call_args_list]
    job_table_sql = next(sql for sql in executed_sql if "CREATE TABLE IF NOT EXISTS ai_batch_jobs" in sql)

    assert "provider VARCHAR(32) NOT NULL DEFAULT 'openai'" in job_table_sql
    assert "UNIQUE KEY uq_ai_batch_jobs_provider_batch_id (provider, batch_id)" in job_table_sql
    assert "INDEX idx_ai_batch_jobs_provider_status_created_at (provider, status, created_at)" in job_table_sql


def test_create_batch_job_with_items_writes_provider_column():
    conn = MagicMock()
    cursor = MagicMock()
    cursor.__enter__ = MagicMock(return_value=cursor)
    cursor.__exit__ = MagicMock(return_value=False)
    cursor.lastrowid = 77
    conn.cursor.return_value = cursor

    job_id = create_batch_job_with_items(
        conn=conn,
        batch_id="batch_123",
        input_file_id="file_123",
        model="gpt-4o-mini",
        bill_ids=["B001", "B002"],
        provider="gemini",
    )

    assert job_id == 77
    insert_sql, insert_params = cursor.execute.call_args_list[0].args
    assert "INSERT INTO ai_batch_jobs (provider, batch_id, status, input_file_id, endpoint, model_name, total_count, submitted_at)" in insert_sql
    assert insert_params[0] == "gemini"


def test_create_batch_job_with_items_uses_legacy_openai_endpoint_by_default():
    conn = MagicMock()
    cursor = MagicMock()
    cursor.__enter__ = MagicMock(return_value=cursor)
    cursor.__exit__ = MagicMock(return_value=False)
    cursor.lastrowid = 88
    conn.cursor.return_value = cursor

    job_id = create_batch_job_with_items(
        conn=conn,
        batch_id="batch_legacy",
        input_file_id="file_legacy",
        model="gpt-4o-mini",
        bill_ids=["B001"],
    )

    assert job_id == 88
    _, insert_params = cursor.execute.call_args_list[0].args
    assert insert_params[4] == "/v1/chat/completions"
    assert insert_params[0] == "openai"


def test_create_batch_job_with_items_accepts_custom_endpoint():
    conn = MagicMock()
    cursor = MagicMock()
    cursor.__enter__ = MagicMock(return_value=cursor)
    cursor.__exit__ = MagicMock(return_value=False)
    cursor.lastrowid = 99
    conn.cursor.return_value = cursor

    create_batch_job_with_items(
        conn=conn,
        batch_id="batch_custom",
        input_file_id="file_custom",
        model="gpt-4o-mini",
        bill_ids=["B001"],
        provider="gemini",
        endpoint="/v1/alt-endpoint",
    )

    _, insert_params = cursor.execute.call_args_list[0].args
    assert insert_params[0] == "gemini"
    assert insert_params[4] == "/v1/alt-endpoint"


def test_openai_batch_provider_build_request_rows_matches_current_openai_shape():
    provider = OpenAIBatchProvider()
    bills = [
        {
            "bill_id": "B001",
            "bill_name": "테스트법",
            "summary": "내용",
            "proposers": "홍길동",
            "proposer_kind": "의원",
            "propose_date": "2024-01-01",
            "stage": "위원회",
        }
    ]

    rows = provider.build_request_rows(bills, model="gpt-4o-mini")
    expected_rows = build_batch_request_rows(bills, model="gpt-4o-mini")

    assert provider.provider_name.value == "openai"
    assert rows == expected_rows


def test_20260419_migration_handles_legacy_index_name_drift():
    migration_sql = Path("infra/db/migrations/20260419_add_provider_to_ai_batch_jobs.sql").read_text()

    assert "INFORMATION_SCHEMA.STATISTICS" in migration_sql
    assert "COLUMN_NAME = 'batch_id'" in migration_sql
    assert "DROP INDEX batch_id" not in migration_sql
