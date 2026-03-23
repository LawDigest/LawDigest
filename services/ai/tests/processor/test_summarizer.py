import pytest
from unittest.mock import MagicMock, patch
import pandas as pd


def test_summarizer_skips_already_summarized():
    from lawdigest_ai.processor.summarizer import AISummarizer
    summarizer = AISummarizer()
    df = pd.DataFrame([{
        "bill_id": "B001", "bill_name": "테스트법", "summary": "내용",
        "brief_summary": "이미 요약됨", "gpt_summary": "상세 요약 있음",
        "proposers": "홍길동", "proposer_kind": "의원발의",
        "proposeDate": "2024-01-01", "stage": "위원회"
    }])
    result = summarizer.AI_structured_summarize(df)
    assert len(result) == 1
    assert result.iloc[0]["brief_summary"] == "이미 요약됨"


def test_summarizer_processes_unsummarized():
    from lawdigest_ai.processor.summarizer import AISummarizer, StructuredBillSummary
    mock_result = StructuredBillSummary(
        brief_summary="요약 제목",
        gpt_summary="상세 요약 내용",
        tags=["세금", "부동산", "의회", "법안", "개정"]
    )
    with patch.object(AISummarizer, "_summarize_one", return_value=mock_result):
        summarizer = AISummarizer()
        df = pd.DataFrame([{
            "bill_id": "B002", "bill_name": "새법안", "summary": "원문",
            "brief_summary": None, "gpt_summary": None,
            "proposers": "김의원", "proposer_kind": "의원발의",
            "proposeDate": "2024-01-01", "stage": "본회의"
        }])
        result = summarizer.AI_structured_summarize(df)
    assert result.iloc[0]["brief_summary"] == "요약 제목"
    assert result.iloc[0]["gpt_summary"] == "상세 요약 내용"
