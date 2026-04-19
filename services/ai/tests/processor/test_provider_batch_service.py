from unittest.mock import MagicMock

from lawdigest_ai.processor.batch_utils import create_batch_job_with_items, ensure_status_tables


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
