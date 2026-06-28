import json
import subprocess
from unittest.mock import patch

import pandas as pd
import pytest


def test_cli_summarizer_defaults_to_codex_model():
    from lawdigest_ai.processor.gemini_cli_summarizer import GeminiCliSummarizer

    summarizer = GeminiCliSummarizer()

    assert summarizer.provider == "codex"
    assert summarizer.model == "gpt-5.4-mini"


def test_gemini_cli_summarizer_processes_unsummarized(capsys):
    from lawdigest_ai.processor.gemini_cli_summarizer import GeminiCliSummarizer

    stdout = json.dumps(
        {
            "response": json.dumps(
                {
                    "briefSummary": "요약 제목",
                    "gptSummary": "상세 요약 내용",
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

    stdout = capsys.readouterr().out
    assert result.iloc[0]["brief_summary"] == "요약 제목"
    assert result.iloc[0]["gpt_summary"] == "상세 요약 내용"
    assert "[cli-summary] codex item 1/1 start bill_id=B002" in stdout
    assert "[cli-summary] codex item 1/1 done bill_id=B002" in stdout


def test_gemini_cli_summarizer_records_failures():
    from lawdigest_ai.processor.gemini_cli_summarizer import GeminiCliSummarizer

    with patch("lawdigest_ai.processor.gemini_cli_summarizer.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(args=["gemini"], returncode=1, stdout="", stderr="auth failed")
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
    assert "codex CLI 실패" in summarizer.failed_bills[0]["error"]


def test_gemini_cli_summarizer_falls_back_to_codex_on_primary_failure():
    from lawdigest_ai.processor.gemini_cli_summarizer import GeminiCliSummarizer

    codex_stdout = json.dumps(
        {
            "briefSummary": "Codex 대체 제목",
            "gptSummary": "Codex 대체 상세",
            "tags": ["대체", "요약", "CLI", "장애", "복구"],
        },
        ensure_ascii=False,
    )

    with patch("lawdigest_ai.processor.gemini_cli_summarizer.subprocess.run") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess(args=["gemini"], returncode=1, stdout="", stderr="quota exceeded"),
            subprocess.CompletedProcess(args=["codex"], returncode=0, stdout=codex_stdout, stderr=""),
        ]
        summarizer = GeminiCliSummarizer(provider="gemini")
        df = pd.DataFrame(
            [
                {
                    "bill_id": "B005",
                    "bill_name": "대체법안",
                    "summary": "원문",
                    "brief_summary": None,
                    "gpt_summary": None,
                    "proposers": "박의원",
                    "proposer_kind": "의원발의",
                }
            ]
        )
        result = summarizer.AI_structured_summarize(df)

    first_command = mock_run.call_args_list[0].args[0]
    second_command = mock_run.call_args_list[1].args[0]
    assert first_command[0] == "gemini"
    assert second_command[:2] == ["codex", "exec"]
    assert "--model" in second_command
    assert "gpt-5.4-mini" in second_command
    assert result.iloc[0]["brief_summary"] == "Codex 대체 제목"
    assert result.iloc[0]["gpt_summary"] == "Codex 대체 상세"
    assert summarizer.failed_bills == []


def test_gemini_cli_summarizer_reuses_api_prompt_and_schema():
    from lawdigest_ai.processor.gemini_cli_summarizer import GeminiCliSummarizer

    summarizer = GeminiCliSummarizer()
    prompt = summarizer._build_user_prompt(
        {
            "bill_id": "B010",
            "bill_name": "동일프롬프트법",
            "summary": "원문",
            "proposers": "김의원",
            "proposer_kind": "의원발의",
        }
    )

    assert "다음 법안 정보를 보고 JSON으로만 응답하세요." in prompt
    assert "키는 briefSummary, gptSummary, tags 세 개만 포함해야 합니다." in prompt
    assert "기존 DB 스타일의 긴 제목형 요약" in prompt
    assert "[핵심 변경 목적/수단]을/를 위한 [정확한 bill_name]" in prompt
    assert "입력 payload의 bill_name과 같은 법안명으로 끝나야 합니다." in prompt
    assert (
        "해양폐기물관리위원회 위원에 지방자치단체 협의체 추천 인사를 포함하기 위한 "
        "해양폐기물 및 해양오염퇴적물 관리법 일부개정법률안"
    ) in prompt
    assert "'입니다', '합니다', '것입니다', '함' 같은 종결 표현으로 끝내지 마세요." in prompt
    assert '"briefSummary"' in prompt
    assert '"gptSummary"' in prompt
    assert "brief_summary/gpt_summary 같은 snake_case 키를 사용하지 마세요." in prompt


def test_gemini_cli_summarizer_rejects_invalid_structured_output():
    from lawdigest_ai.processor.gemini_cli_summarizer import GeminiCliSummarizer

    stdout = json.dumps(
        {
            "briefSummary": "요약 제목",
            "gptSummary": "상세 요약 내용",
            "tags": ["세금", "부동산"],
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
                    "bill_id": "B011",
                    "bill_name": "스키마실패법안",
                    "summary": "원문",
                    "brief_summary": None,
                    "gpt_summary": None,
                }
            ]
        )
        result = summarizer.AI_structured_summarize(df)

    assert pd.isna(result.iloc[0]["brief_summary"])
    assert len(summarizer.failed_bills) == 1
    assert "구조화 응답 검증 실패" in summarizer.failed_bills[0]["error"]


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
            "briefSummary": "CLI 제목",
            "gptSummary": "CLI 상세",
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
