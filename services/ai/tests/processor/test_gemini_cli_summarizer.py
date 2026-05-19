import json
import subprocess
from unittest.mock import patch

import pandas as pd
import pytest


def test_gemini_cli_summarizer_processes_unsummarized():
    from lawdigest_ai.processor.gemini_cli_summarizer import GeminiCliSummarizer

    stdout = json.dumps(
        {
            "response": json.dumps(
                {
                    "brief_summary": "요약 제목",
                    "gpt_summary": "상세 요약 내용",
                    "tags": ["세금", "부동산", "의회", "법안", "개정"],
                },
                ensure_ascii=False,
            )
        },
        ensure_ascii=False,
    )

    with patch("lawdigest_ai.processor.gemini_cli_summarizer.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gemini"],
            returncode=0,
            stdout=stdout,
            stderr="",
        )
        summarizer = GeminiCliSummarizer()
        df = pd.DataFrame(
            [
                {
                    "bill_id": "B002",
                    "bill_name": "새법안",
                    "summary": "원문",
                    "brief_summary": None,
                    "gpt_summary": None,
                    "proposers": "김의원",
                    "proposer_kind": "의원발의",
                    "proposeDate": "2024-01-01",
                    "stage": "본회의",
                }
            ]
        )
        result = summarizer.AI_structured_summarize(df)

    assert result.iloc[0]["brief_summary"] == "요약 제목"
    assert result.iloc[0]["gpt_summary"] == "상세 요약 내용"


def test_gemini_cli_summarizer_records_failures():
    from lawdigest_ai.processor.gemini_cli_summarizer import GeminiCliSummarizer

    with patch("lawdigest_ai.processor.gemini_cli_summarizer.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gemini"],
            returncode=1,
            stdout="",
            stderr="auth failed",
        )
        summarizer = GeminiCliSummarizer()
        df = pd.DataFrame(
            [
                {
                    "bill_id": "B003",
                    "bill_name": "실패법안",
                    "summary": "원문",
                    "brief_summary": None,
                    "gpt_summary": None,
                }
            ]
        )
        result = summarizer.AI_structured_summarize(df)

    assert pd.isna(result.iloc[0]["brief_summary"])
    assert len(summarizer.failed_bills) == 1
    assert summarizer.failed_bills[0]["bill_id"] == "B003"


@pytest.mark.parametrize(
    ("provider", "expected_tokens"),
    [
        ("gemini", ["--prompt", "--approval-mode", "yolo"]),
        ("codex", ["exec", "--sandbox", "read-only"]),
        ("claude", ["--print", "--output-format", "text"]),
    ],
)
def test_cli_summarizer_runs_provider_headless_command(provider, expected_tokens):
    from lawdigest_ai.processor.gemini_cli_summarizer import build_cli_summarizer

    stdout = json.dumps(
        {
            "brief_summary": "CLI 제목",
            "gpt_summary": "CLI 상세",
            "tags": ["정책", "법안", "국회", "개정", "제도"],
        },
        ensure_ascii=False,
    )

    with patch("lawdigest_ai.processor.gemini_cli_summarizer.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[provider],
            returncode=0,
            stdout=stdout,
            stderr="",
        )
        summarizer = build_cli_summarizer(provider)
        df = pd.DataFrame(
            [
                {
                    "bill_id": "B004",
                    "bill_name": "CLI 법안",
                    "summary": "원문",
                    "brief_summary": None,
                    "gpt_summary": None,
                    "proposers": "최의원",
                    "proposer_kind": "의원발의",
                }
            ]
        )
        result = summarizer.AI_structured_summarize(df)

    command = mock_run.call_args.args[0]
    assert all(token in command for token in expected_tokens)
    assert result.iloc[0]["brief_summary"] == "CLI 제목"
