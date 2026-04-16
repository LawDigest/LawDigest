import pytest
from unittest.mock import MagicMock, patch
import pandas as pd


def test_instant_summarize_returns_summary():
    from lawdigest_ai.processor.instant_summarizer import summarize_single_bill
    mock_df = pd.DataFrame([{
        "bill_id": "B001", "brief_summary": "요약", "gpt_summary": "상세",
        "summary_tags": '["a","b","c","d","e"]'
    }])
    with patch("lawdigest_ai.processor.instant_summarizer.AISummarizer") as MockSummarizer:
        instance = MockSummarizer.return_value
        instance.AI_structured_summarize.return_value = mock_df
        result = summarize_single_bill({"bill_id": "B001", "summary": "원문 내용"})
    assert result["brief_summary"] == "요약"


def test_gemini_cli_instant_summarize_returns_summary():
    from lawdigest_ai.processor.instant_summarizer import summarize_single_bill_with_gemini_cli
    mock_df = pd.DataFrame([{
        "bill_id": "B001", "brief_summary": "CLI 요약", "gpt_summary": "CLI 상세",
        "summary_tags": '["a","b","c","d","e"]'
    }])
    with patch("lawdigest_ai.processor.instant_summarizer.GeminiCliSummarizer") as MockSummarizer:
        instance = MockSummarizer.return_value
        instance.AI_structured_summarize.return_value = mock_df
        result = summarize_single_bill_with_gemini_cli({"bill_id": "B001", "summary": "원문 내용"})
    assert result["brief_summary"] == "CLI 요약"


def test_batch_submit_dry_run():
    from lawdigest_ai.processor.batch_submit import submit_batch
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_cursor.fetchall.return_value = [
        {"bill_id": "B001", "bill_name": "테스트법", "summary": "내용",
         "proposers": "홍길동", "proposer_kind": "의원", "propose_date": "2024-01-01", "stage": "위원회"}
    ]
    mock_conn.cursor.return_value = mock_cursor

    with patch("lawdigest_ai.processor.batch_submit.get_db_connection", return_value=mock_conn):
        result = submit_batch(limit=10, model="gpt-4o-mini", mode="dry_run")
    assert result["mode"] == "dry_run"
    assert result["submitted"] >= 0


def test_batch_ingest_dry_run():
    from lawdigest_ai.processor.batch_ingest import ingest_batch_results
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_cursor.fetchall.return_value = []
    mock_conn.cursor.return_value = mock_cursor

    with patch("lawdigest_ai.processor.batch_ingest.get_db_connection", return_value=mock_conn):
        result = ingest_batch_results(max_jobs=5, mode="dry_run")
    assert result["processed_jobs"] == 0
    assert result["mode"] == "dry_run"
