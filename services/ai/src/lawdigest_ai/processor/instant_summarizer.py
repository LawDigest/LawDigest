from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from lawdigest_ai.processor.summarizer import AISummarizer


def summarize_single_bill(bill_data: Dict[str, Any]) -> Dict[str, Any]:
    """단일 법안에 대해 AI 요약을 수행하고 결과 dict를 반환합니다."""
    df = pd.DataFrame([bill_data])
    summarizer = AISummarizer()
    result_df = summarizer.AI_structured_summarize(df)
    return result_df.to_dict("records")[0]


def summarize_bills(bills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """복수의 법안에 대해 AI 요약을 수행하고 결과 리스트를 반환합니다."""
    df = pd.DataFrame(bills)
    summarizer = AISummarizer()
    result_df = summarizer.AI_structured_summarize(df)
    return result_df.to_dict("records")
