from unittest.mock import MagicMock

from lawdigest_ai.processor.batch_utils import (
    create_batch_job_with_items,
    ensure_status_tables,
)
from lawdigest_ai.processor.providers.openai_batch import OpenAIBatchProvider
from lawdigest_ai.processor.providers.types import (
    BatchProviderJobState,
    BatchProviderParseResult,
    ProviderName,
)


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

    assert provider.provider_name == ProviderName.OPENAI
    assert len(rows) == 1

    row = rows[0]
    assert row["custom_id"] == "B001"
    assert row["method"] == "POST"
    assert row["url"] == "/v1/chat/completions"

    body = row["body"]
    assert body["model"] == "gpt-4o-mini"
    assert body["temperature"] == 0.2

    messages = body["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "한국 법안 요약 전문가" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert "B001" in messages[1]["content"]
    assert "테스트법" in messages[1]["content"]
    assert "홍길동" in messages[1]["content"]
    assert "의원" in messages[1]["content"]
    assert "2024-01-01" in messages[1]["content"]
    assert "위원회" in messages[1]["content"]
    assert "내용" in messages[1]["content"]

    response_format = body["response_format"]
    assert response_format["type"] == "json_schema"
    json_schema = response_format["json_schema"]
    assert json_schema["name"] == "bill_summary"
    assert json_schema["strict"] is True
    schema = json_schema["schema"]
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {"briefSummary", "gptSummary", "tags"}
    assert set(schema["properties"]) == {"briefSummary", "gptSummary", "tags"}


def test_submit_batches_routes_to_requested_provider(tmp_path):
    from lawdigest_ai.processor.provider_batch_service import submit_batches

    conn = MagicMock()
    create_job_calls = []
    provider = MagicMock()
    provider.provider_name = ProviderName.GEMINI
    provider.build_request_rows.return_value = [{"key": "B001"}]
    provider.upload_batch_file.return_value = "files/gemini-input.jsonl"
    provider.create_batch_job.return_value = BatchProviderJobState(
        batch_id="batches/gemini-123",
        status="SUBMITTED",
        output_file_id=None,
        error_file_id=None,
        error_message=None,
    )
    bills = [{"bill_id": "B001", "summary": "내용"}]

    result = submit_batches(
        conn=conn,
        provider="gemini",
        limit=10,
        model="gemini-2.5-flash",
        mode="test",
        fetch_bills=lambda current_conn, limit: bills,
        provider_factory=lambda requested_provider: provider,
        jsonl_writer=lambda rows: str(tmp_path / "requests.jsonl"),
        create_job=lambda **kwargs: create_job_calls.append(kwargs) or 501,
    )

    assert result == {
        "submitted": 1,
        "batch_id": "batches/gemini-123",
        "job_id": 501,
        "mode": "test",
        "provider": "gemini",
    }
    provider.build_request_rows.assert_called_once_with(bills, model="gemini-2.5-flash")
    provider.upload_batch_file.assert_called_once_with(str(tmp_path / "requests.jsonl"), display_name=None)
    provider.create_batch_job.assert_called_once_with(
        model="gemini-2.5-flash",
        source_file_name="files/gemini-input.jsonl",
        display_name=None,
    )
    create_job_call = create_job_calls[0]
    assert create_job_call["provider"] == "gemini"
    assert create_job_call["endpoint"] == "/v1/chat/completions"


def test_submit_batches_uses_openai_defaults_for_backward_compatibility(tmp_path):
    from lawdigest_ai.processor.provider_batch_service import submit_batches

    conn = MagicMock()
    create_job_calls = []
    provider = MagicMock()
    provider.provider_name = ProviderName.OPENAI
    provider.build_request_rows.return_value = [{"custom_id": "B001", "url": "/v1/chat/completions"}]
    provider.upload_batch_file.return_value = "file-openai-123"
    provider.create_batch_job.return_value = BatchProviderJobState(
        batch_id="batch-openai-123",
        status="VALIDATING",
        output_file_id=None,
        error_file_id=None,
        error_message=None,
    )
    bills = [{"bill_id": "B001", "summary": "내용"}]

    result = submit_batches(
        conn=conn,
        provider="openai",
        limit=10,
        model="gpt-4o-mini",
        mode="test",
        fetch_bills=lambda current_conn, limit: bills,
        provider_factory=lambda requested_provider: provider,
        jsonl_writer=lambda rows: str(tmp_path / "requests.jsonl"),
        create_job=lambda **kwargs: create_job_calls.append(kwargs) or 502,
    )

    assert result["provider"] == "openai"
    create_job_call = create_job_calls[0]
    assert create_job_call["provider"] == "openai"
    assert create_job_call["endpoint"] == "/v1/chat/completions"


def test_ingest_batch_results_filters_jobs_by_provider_and_processes_all():
    from lawdigest_ai.processor.provider_batch_service import ingest_batch_results_for_provider

    conn = MagicMock()
    fetch_jobs_calls = []
    update_status_calls = []
    openai_provider = MagicMock()
    openai_provider.provider_name = ProviderName.OPENAI
    openai_provider.get_batch_job.return_value = BatchProviderJobState(
        batch_id="batch-openai",
        status="COMPLETED",
        output_file_id="openai-output",
        error_file_id=None,
        error_message=None,
    )
    openai_provider.download_output_file.return_value = "openai-jsonl"

    gemini_provider = MagicMock()
    gemini_provider.provider_name = ProviderName.GEMINI
    gemini_provider.get_batch_job.return_value = BatchProviderJobState(
        batch_id="batch-gemini",
        status="COMPLETED",
        output_file_id="gemini-output",
        error_file_id=None,
        error_message=None,
    )
    gemini_provider.download_output_file.return_value = "gemini-jsonl"

    jobs = [
        {"id": 1, "provider": "openai", "batch_id": "batch-openai"},
        {"id": 2, "provider": "gemini", "batch_id": "batch-gemini"},
    ]

    result = ingest_batch_results_for_provider(
        conn=conn,
        provider="all",
        max_jobs=5,
        mode="test",
        fetch_jobs=lambda current_conn, max_jobs, provider: fetch_jobs_calls.append(
            {"max_jobs": max_jobs, "provider": provider}
        )
        or jobs,
        provider_factory=lambda requested_provider: {
            "openai": openai_provider,
            "gemini": gemini_provider,
        }[requested_provider],
        apply_results=lambda current_conn, job_id, output_jsonl, provider_instance: (2, 0)
        if job_id == 1
        else (3, 1),
        update_status=lambda **kwargs: update_status_calls.append(kwargs),
    )

    assert result == {
        "processed_jobs": 2,
        "total_success": 5,
        "total_failed": 1,
        "mode": "test",
        "provider": "all",
    }
    assert fetch_jobs_calls == [{"max_jobs": 5, "provider": None}]
    openai_provider.get_batch_job.assert_called_once_with("batch-openai")
    gemini_provider.get_batch_job.assert_called_once_with("batch-gemini")
    assert update_status_calls == [
        {
            "conn": conn,
            "job_id": 1,
            "status": "COMPLETED",
            "output_file_id": "openai-output",
            "error_file_id": None,
            "error_message": None,
        },
        {
            "conn": conn,
            "job_id": 2,
            "status": "COMPLETED",
            "output_file_id": "gemini-output",
            "error_file_id": None,
            "error_message": None,
        },
    ]


def test_ingest_batch_results_uses_provider_filter_for_single_provider():
    from lawdigest_ai.processor.provider_batch_service import ingest_batch_results_for_provider

    conn = MagicMock()
    fetch_jobs_calls = []

    result = ingest_batch_results_for_provider(
        conn=conn,
        provider="gemini",
        max_jobs=3,
        mode="dry_run",
        fetch_jobs=lambda current_conn, max_jobs, provider: fetch_jobs_calls.append(
            {"max_jobs": max_jobs, "provider": provider}
        )
        or [],
    )

    assert result == {
        "processed_jobs": 0,
        "mode": "dry_run",
        "provider": "gemini",
    }
    assert fetch_jobs_calls == [{"max_jobs": 3, "provider": "gemini"}]


def test_ingest_batch_results_passes_provider_parser_into_apply_results():
    from lawdigest_ai.processor.provider_batch_service import ingest_batch_results_for_provider

    conn = MagicMock()
    provider = MagicMock()
    provider.provider_name = ProviderName.GEMINI
    provider.get_batch_job.return_value = BatchProviderJobState(
        batch_id="batch-gemini",
        status="COMPLETED",
        output_file_id="gemini-output",
        error_file_id=None,
        error_message=None,
    )
    provider.download_output_file.return_value = "gemini-jsonl"

    captured = {}

    def fake_apply(current_conn, job_id, output_jsonl, provider_instance):
        captured["provider"] = provider_instance
        return (1, 0)

    result = ingest_batch_results_for_provider(
        conn=conn,
        provider="gemini",
        max_jobs=1,
        mode="test",
        fetch_jobs=lambda current_conn, max_jobs, provider: [
            {"id": 99, "provider": "gemini", "batch_id": "batch-gemini"}
        ],
        provider_factory=lambda requested_provider: provider,
        apply_results=fake_apply,
    )

    assert result["processed_jobs"] == 1
    assert captured["provider"] is provider


def test_provider_batch_apply_results_uses_provider_parse_output_lines():
    from lawdigest_ai.processor.provider_batch_service import apply_batch_results_for_provider

    conn = MagicMock()
    cursor = MagicMock()
    cursor.__enter__ = MagicMock(return_value=cursor)
    cursor.__exit__ = MagicMock(return_value=False)
    cursor.fetchall.return_value = [{"bill_id": "B001"}]
    cursor.rowcount = 0
    conn.cursor.return_value = cursor

    provider = MagicMock()
    provider.parse_output_lines.return_value = [
        BatchProviderParseResult(
            bill_id="B001",
            brief_summary="짧은 요약",
            gpt_summary="긴 요약",
            tags=["a", "b", "c", "d", "e"],
            error=None,
        )
    ]

    success, failed = apply_batch_results_for_provider(
        conn=conn,
        job_id=1,
        output_jsonl="{}",
        provider=provider,
    )

    assert (success, failed) == (1, 0)
    provider.parse_output_lines.assert_called_once_with("{}", expected_bill_ids=["B001"])
