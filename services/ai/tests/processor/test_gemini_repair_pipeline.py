from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest


def _mock_connection(rows):
    conn = MagicMock()
    cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchall.return_value = rows
    return conn


def test_gemini_repair_pipeline_saves_json_in_dry_run(tmp_path):
    from lawdigest_ai.processor.gemini_repair_pipeline import run_gemini_repair_pipeline

    rows = [{
        "bill_id": "B001",
        "bill_name": "개인정보 보호법 일부개정법률안",
        "summary": "원문 요약",
        "proposers": "홍길동",
        "proposer_kind": "의원발의",
        "brief_summary": None,
        "gpt_summary": None,
        "propose_date": "2026-04-16",
        "stage": "위원회",
    }]
    result_rows = [{
        **rows[0],
        "brief_summary": "개인정보 처리 투명성 강화",
        "gpt_summary": "1. 처리방침 고지 의무를 강화한다.",
        "summary_tags": json.dumps(["개인정보보호", "투명성강화", "정보주체권리", "설명요구권", "제재기준정비"], ensure_ascii=False),
    }]
    output_path = tmp_path / "gemini-repair.json"

    with patch("lawdigest_ai.processor.gemini_repair_pipeline.get_db_connection", return_value=_mock_connection(rows)), \
         patch("lawdigest_ai.processor.gemini_repair_pipeline.update_bill_summary") as mock_update, \
         patch("lawdigest_ai.processor.gemini_repair_pipeline.GeminiCliSummarizer") as MockSummarizer:
        MockSummarizer.return_value.failed_bills = []
        MockSummarizer.return_value.AI_structured_summarize.return_value = pd.DataFrame(result_rows)

        report = run_gemini_repair_pipeline(
            mode="dry_run",
            limit=10,
            batch_size=5,
            output_path=str(output_path),
        )

    saved = json.loads(Path(output_path).read_text(encoding="utf-8"))
    assert report["stats"]["success_count"] == 1
    assert saved["items"][0]["ai_title"] == "개인정보 처리 투명성 강화"
    assert saved["stats"]["db_upserted_count"] == 0
    mock_update.assert_not_called()


def test_gemini_repair_pipeline_upserts_successful_items():
    from lawdigest_ai.processor.gemini_repair_pipeline import run_gemini_repair_pipeline

    rows = [{
        "bill_id": "B002",
        "bill_name": "플랫폼 공정화법안",
        "summary": "원문 요약",
        "proposers": "김철수",
        "proposer_kind": "의원발의",
        "brief_summary": "",
        "gpt_summary": None,
        "propose_date": "2026-04-16",
        "stage": "본회의",
    }]
    result_rows = [{
        **rows[0],
        "brief_summary": "플랫폼 거래 투명성 강화",
        "gpt_summary": "1. 계약조건 공개 의무를 확대한다.",
        "summary_tags": json.dumps(["플랫폼규제", "거래투명성", "공정거래", "계약공개", "사업자책임"], ensure_ascii=False),
    }]

    with patch("lawdigest_ai.processor.gemini_repair_pipeline.get_db_connection", return_value=_mock_connection(rows)), \
         patch("lawdigest_ai.processor.gemini_repair_pipeline.update_bill_summary") as mock_update, \
         patch("lawdigest_ai.processor.gemini_repair_pipeline.GeminiCliSummarizer") as MockSummarizer:
        MockSummarizer.return_value.failed_bills = []
        MockSummarizer.return_value.AI_structured_summarize.return_value = pd.DataFrame(result_rows)

        report = run_gemini_repair_pipeline(
            mode="test",
            limit=10,
            batch_size=5,
            output_path="/tmp/test-gemini-repair.json",
        )

    assert report["stats"]["db_upserted_count"] == 1
    mock_update.assert_called_once()


def test_gemini_repair_pipeline_raises_when_all_items_fail(tmp_path):
    from lawdigest_ai.processor.gemini_repair_pipeline import run_gemini_repair_pipeline

    rows = [{
        "bill_id": "B003",
        "bill_name": "실패 법안",
        "summary": "원문 요약",
        "proposers": "박영희",
        "proposer_kind": "의원발의",
        "brief_summary": None,
        "gpt_summary": None,
        "propose_date": "2026-04-16",
        "stage": "위원회",
    }]
    output_path = tmp_path / "failed-gemini-repair.json"

    with patch("lawdigest_ai.processor.gemini_repair_pipeline.get_db_connection", return_value=_mock_connection(rows)), \
         patch("lawdigest_ai.processor.gemini_repair_pipeline.GeminiCliSummarizer") as MockSummarizer:
        MockSummarizer.return_value.failed_bills = [{"bill_id": "B003", "error": "timeout"}]
        MockSummarizer.return_value.AI_structured_summarize.return_value = pd.DataFrame(rows)

        with pytest.raises(RuntimeError):
            run_gemini_repair_pipeline(
                mode="dry_run",
                limit=10,
                batch_size=5,
                output_path=str(output_path),
            )

    saved = json.loads(Path(output_path).read_text(encoding="utf-8"))
    assert saved["stats"]["failure_count"] == 1
    assert saved["items"][0]["status"] == "failed"
