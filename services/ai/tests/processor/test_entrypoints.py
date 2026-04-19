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

    with (
        patch("lawdigest_ai.processor.batch_submit.get_db_connection", return_value=mock_conn),
        patch(
            "lawdigest_ai.processor.batch_submit.submit_batches",
            return_value={"submitted": 3, "mode": "dry_run", "provider": "openai"},
        ) as submit_batches,
    ):
        result = submit_batch(limit=10, model="gpt-4o-mini", mode="dry_run")

    assert result == {"submitted": 3, "mode": "dry_run", "provider": "openai"}
    submit_batches.assert_called_once_with(
        conn=mock_conn,
        limit=10,
        model="gpt-4o-mini",
        mode="dry_run",
        provider="openai",
    )
    mock_conn.close.assert_called_once()


def test_batch_submit_accepts_provider_param():
    from lawdigest_ai.processor.batch_submit import submit_batch

    mock_conn = MagicMock()

    with (
        patch("lawdigest_ai.processor.batch_submit.get_db_connection", return_value=mock_conn),
        patch(
            "lawdigest_ai.processor.batch_submit.submit_batches",
            return_value={"submitted": 1, "mode": "test", "provider": "gemini"},
        ) as submit_batches,
    ):
        result = submit_batch(limit=5, model="gemini-2.5-flash", mode="test", provider="gemini")

    assert result["provider"] == "gemini"
    submit_batches.assert_called_once_with(
        conn=mock_conn,
        limit=5,
        model="gemini-2.5-flash",
        mode="test",
        provider="gemini",
    )
    mock_conn.close.assert_called_once()


def test_batch_ingest_dry_run():
    from lawdigest_ai.processor.batch_ingest import ingest_batch_results
    mock_conn = MagicMock()

    with (
        patch("lawdigest_ai.processor.batch_ingest.get_db_connection", return_value=mock_conn),
        patch(
            "lawdigest_ai.processor.batch_ingest.ingest_batch_results_for_provider",
            return_value={"processed_jobs": 0, "mode": "dry_run", "provider": "all"},
        ) as ingest_for_provider,
    ):
        result = ingest_batch_results(max_jobs=5, mode="dry_run")

    assert result == {"processed_jobs": 0, "mode": "dry_run", "provider": "all"}
    ingest_for_provider.assert_called_once_with(
        conn=mock_conn,
        max_jobs=5,
        mode="dry_run",
        provider="all",
    )
    mock_conn.close.assert_called_once()


def test_batch_ingest_accepts_provider_param():
    from lawdigest_ai.processor.batch_ingest import ingest_batch_results

    mock_conn = MagicMock()

    with (
        patch("lawdigest_ai.processor.batch_ingest.get_db_connection", return_value=mock_conn),
        patch(
            "lawdigest_ai.processor.batch_ingest.ingest_batch_results_for_provider",
            return_value={"processed_jobs": 1, "mode": "test", "provider": "gemini"},
        ) as ingest_for_provider,
    ):
        result = ingest_batch_results(max_jobs=2, mode="test", provider="gemini")

    assert result["provider"] == "gemini"
    ingest_for_provider.assert_called_once_with(
        conn=mock_conn,
        max_jobs=2,
        mode="test",
        provider="gemini",
    )
    mock_conn.close.assert_called_once()
