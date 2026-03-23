import json
import pytest
from unittest.mock import MagicMock
from lawdigest_ai.processor.batch_utils import (
    build_batch_request_rows,
    parse_output_jsonl_line,
    apply_batch_results,
    BatchStructuredSummary,
)


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
