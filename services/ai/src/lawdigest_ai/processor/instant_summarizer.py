from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from lawdigest_ai.processor.gemini_cli_summarizer import GeminiCliSummarizer

try:
    from lawdigest_ai.processor.summarizer import AISummarizer
except Exception:
    # pydantic-ai import can fail at module import time in some environments.
    # Keep the symbol patchable for tests and import lazily when needed.
    AISummarizer = None


def _write_json_output(payload: Any, output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _normalize_summary_keys(payload: Dict[str, Any]) -> Dict[str, Any]:
    return dict(payload)


def _normalize_summary_keys_list(payload: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [_normalize_summary_keys(item) for item in payload]


def summarize_single_bill(bill_data: Dict[str, Any]) -> Dict[str, Any]:
    """단일 법안에 대해 AI 요약을 수행하고 결과 dict를 반환합니다."""
    df = pd.DataFrame([bill_data])
    summarizer_cls = AISummarizer
    if summarizer_cls is None:
        from lawdigest_ai.processor.summarizer import AISummarizer as summarizer_cls
    summarizer = summarizer_cls()
    result_df = summarizer.AI_structured_summarize(df)
    return _normalize_summary_keys(result_df.to_dict("records")[0])


def summarize_bills(bills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """복수의 법안에 대해 AI 요약을 수행하고 결과 리스트를 반환합니다."""
    df = pd.DataFrame(bills)
    summarizer_cls = AISummarizer
    if summarizer_cls is None:
        from lawdigest_ai.processor.summarizer import AISummarizer as summarizer_cls
    summarizer = summarizer_cls()
    result_df = summarizer.AI_structured_summarize(df)
    return _normalize_summary_keys_list(result_df.to_dict("records"))


def summarize_single_bill_with_gemini_cli(
    bill_data: Dict[str, Any],
    output_path: str | None = None,
) -> Dict[str, Any]:
    """단일 법안에 대해 Gemini CLI 기반 요약을 수행하고 결과 dict를 반환합니다."""
    df = pd.DataFrame([bill_data])
    summarizer = GeminiCliSummarizer()
    result_df = summarizer.AI_structured_summarize(df)
    result = _normalize_summary_keys(result_df.to_dict("records")[0])
    if output_path:
        _write_json_output(result, output_path)
    return result


def summarize_bills_with_gemini_cli(
    bills: List[Dict[str, Any]],
    output_path: str | None = None,
) -> List[Dict[str, Any]]:
    """복수의 법안에 대해 Gemini CLI 기반 요약을 수행하고 결과 리스트를 반환합니다."""
    df = pd.DataFrame(bills)
    summarizer = GeminiCliSummarizer()
    result_df = summarizer.AI_structured_summarize(df)
    result = _normalize_summary_keys_list(result_df.to_dict("records"))
    if output_path:
        _write_json_output(result, output_path)
    return result
