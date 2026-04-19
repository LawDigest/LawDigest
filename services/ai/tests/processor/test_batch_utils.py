import json
from unittest.mock import MagicMock

from lawdigest_ai.processor.batch_utils import (
    build_batch_request_rows,
    parse_output_jsonl_line,
    apply_batch_results,
    openai_create_batch,
    openai_get_batch,
)
from lawdigest_ai.processor.providers.openai_batch import BatchStructuredSummary, OpenAIBatchProvider
from lawdigest_ai.processor.providers.types import BatchProviderJobState


def test_build_batch_request_rows_structure():
    bills = [{"bill_id": "B001", "bill_name": "테스트법", "summary": "내용",
               "proposers": "홍길동", "proposer_kind": "의원", "propose_date": "2024-01-01", "stage": "위원회"}]
    rows = build_batch_request_rows(bills, model="gpt-4o-mini")
    assert len(rows) == 1
    assert rows[0]["custom_id"] == "B001"
    assert rows[0]["body"]["model"] == "gpt-4o-mini"


def test_parse_output_jsonl_line_success():
    summary = BatchStructuredSummary(
        brief_summary="요약", gpt_summary="상세", tags=["a", "b", "c", "d", "e"]
    )
    content = summary.model_dump_json(by_alias=True)
    line = json.dumps({
        "custom_id": "B001",
        "response": {
            "status_code": 200,
            "body": {"choices": [{"message": {"content": content}}]}
        }
    })
    bill_id, brief, gpt, tags, err = parse_output_jsonl_line(line)
    assert bill_id == "B001"
    assert brief == "요약"
    assert err is None


def test_parse_output_jsonl_line_error():
    line = json.dumps({
        "custom_id": "B001",
        "response": {"status_code": 500, "body": {}}
    })
    bill_id, brief, gpt, tags, err = parse_output_jsonl_line(line)
    assert err is not None
    assert brief is None


def test_parse_output_jsonl_line_surfaces_top_level_openai_error():
    line = json.dumps({
        "custom_id": "B001",
        "error": {"code": "invalid_request_error", "message": "row failed before response"},
    })

    bill_id, brief, gpt, tags, err = parse_output_jsonl_line(line)

    assert bill_id == "B001"
    assert brief is None
    assert gpt is None
    assert tags is None
    assert err == "row failed before response"


def test_apply_batch_results_success_and_partial_failure():
    """성공 라인과 실패 라인이 섞인 JSONL에서 각각 올바르게 처리되는지 확인."""
    summary = BatchStructuredSummary(
        brief_summary="요약", gpt_summary="상세", tags=["a", "b", "c", "d", "e"]
    )
    success_line = json.dumps({
        "custom_id": "B001",
        "response": {"status_code": 200, "body": {"choices": [{"message": {"content": summary.model_dump_json(by_alias=True)}}]}}
    })
    fail_line = json.dumps({
        "custom_id": "B002",
        "response": {"status_code": 500, "body": {}}
    })
    output_jsonl = success_line + "\n" + fail_line

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_cursor.rowcount = 0
    mock_conn.cursor.return_value = mock_cursor

    success, failed = apply_batch_results(mock_conn, job_id=1, output_jsonl=output_jsonl)
    assert success == 1
    assert failed == 1


def test_openai_batch_utils_preserve_legacy_dict_contract(monkeypatch):
    state = BatchProviderJobState(
        batch_id="batch_123",
        status="COMPLETED",
        output_file_id="file_out_123",
        error_file_id="file_err_123",
        error_message="partial failure",
    )

    create_mock = MagicMock(return_value=state)
    get_mock = MagicMock(return_value=state)
    monkeypatch.setattr(
        "lawdigest_ai.processor.batch_utils.OpenAIBatchProvider.create_batch_job",
        create_mock,
    )
    monkeypatch.setattr(
        "lawdigest_ai.processor.batch_utils.OpenAIBatchProvider.get_batch_job",
        get_mock,
    )

    created = openai_create_batch(input_file_id="file_in_123", model="gpt-4o-mini")
    fetched = openai_get_batch("batch_123")

    assert created == {
        "id": "batch_123",
        "status": "completed",
        "output_file_id": "file_out_123",
        "error_file_id": "file_err_123",
        "error_message": "partial failure",
    }
    assert fetched == created
    create_mock.assert_called_once_with(model="gpt-4o-mini", source_file_name="file_in_123")
    get_mock.assert_called_once_with("batch_123")


def test_openai_batch_provider_normalizes_canceling_and_cancelled_statuses(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class _FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    responses = [
        _FakeResponse({"id": "batch_123", "status": "cancelling"}),
        _FakeResponse({"id": "batch_456", "status": "cancelled"}),
    ]
    get_mock = MagicMock(side_effect=responses)
    monkeypatch.setattr("lawdigest_ai.processor.providers.openai_batch.requests.get", get_mock)

    provider = OpenAIBatchProvider()

    canceling = provider.get_batch_job("batch_123")
    cancelled = provider.get_batch_job("batch_456")

    assert canceling.status == "CANCELLING"
    assert cancelled.status == "CANCELED"
