from unittest.mock import patch
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


def test_pydantic_ai_summarizer_reuses_batch_prompt():
    from lawdigest_ai.processor.summarizer import AISummarizer

    summarizer = AISummarizer()
    prompt = summarizer._build_user_prompt({
        "bill_id": "B010",
        "bill_name": "동일프롬프트법",
        "summary": "원문",
        "proposers": "김의원",
        "proposer_kind": "의원발의",
    })

    assert "다음 법안 정보를 보고 JSON으로만 응답하세요." in prompt
    assert "키는 briefSummary, gptSummary, tags 세 개만 포함해야 합니다." in prompt
    assert "briefSummary는 정확한 bill_name을 포함하되 전체를 짧은 제목형 명사구로 작성하세요." in prompt
    assert "briefSummary는 짧은 핵심 문구와 정확한 bill_name만 조합하세요." in prompt
    assert "1. **핵심 항목명**: 설명" in prompt
    assert "중요한 제도명, 수치, 대상, 변경 내용은 **굵게** 표시하세요." in prompt
    assert "김의원 등 1명에 의해 발의된 ‘동일프롬프트법’ 법안의 주요 내용은 다음과 같습니다:" in prompt
    assert "{opening_proposer_line}" not in prompt
