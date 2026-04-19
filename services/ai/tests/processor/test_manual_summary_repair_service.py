from __future__ import annotations

import json
from unittest.mock import MagicMock, patch


def _mock_connection(rows):
    conn = MagicMock()
    cursor = MagicMock()
    cursor.fetchall.return_value = rows
    conn.cursor.return_value.__enter__.return_value = cursor
    return conn


def test_manual_summary_repair_saves_report_in_dry_run(tmp_path):
    from lawdigest_ai.processor.manual_summary_repair_service import run_manual_summary_repair

    rows = [
        {
            "bill_id": "B001",
            "bill_name": "법안1",
            "summary": "원문1",
            "proposers": "홍길동",
            "proposer_kind": "CONGRESSMAN",
            "brief_summary": None,
            "gpt_summary": None,
            "propose_date": "2026-04-19",
            "stage": "접수",
        },
        {
            "bill_id": "B002",
            "bill_name": "법안2",
            "summary": "원문2",
            "proposers": "임꺽정",
            "proposer_kind": "CONGRESSMAN",
            "brief_summary": None,
            "gpt_summary": None,
            "propose_date": "2026-04-18",
            "stage": "접수",
        },
    ]
    output_path = tmp_path / "manual-repair.json"

    with (
        patch(
            "lawdigest_ai.processor.manual_summary_repair_service.get_db_connection",
            return_value=_mock_connection(rows),
        ),
        patch(
            "lawdigest_ai.processor.manual_summary_repair_service.summarize_bills_with_provider",
            return_value=[
                {
                    "bill_id": "B001",
                    "brief_summary": "요약1",
                    "gpt_summary": "상세1",
                    "summary_tags": '["a","b","c","d","e"]',
                    "error": None,
                },
                {
                    "bill_id": "B002",
                    "brief_summary": None,
                    "gpt_summary": None,
                    "summary_tags": None,
                    "error": "요약 실패",
                },
            ],
        ) as summarize_bills,
        patch("lawdigest_ai.processor.manual_summary_repair_service.update_bill_summary") as mock_update,
    ):
        report = run_manual_summary_repair(
            mode="dry_run",
            output_path=str(output_path),
            batch_size=10,
            provider="gemini",
            model=None,
        )

    summarize_bills.assert_called_once()
    assert report["provider"] == "gemini"
    assert report["stats"]["target_count"] == 2
    assert report["stats"]["success_count"] == 1
    assert report["stats"]["failure_count"] == 1
    mock_update.assert_not_called()

    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert saved["items"][0]["status"] == "success"
    assert saved["items"][1]["status"] == "failed"


def test_manual_summary_repair_upserts_successful_items():
    from lawdigest_ai.processor.manual_summary_repair_service import run_manual_summary_repair

    rows = [
        {
            "bill_id": "B001",
            "bill_name": "법안1",
            "summary": "원문1",
            "proposers": "홍길동",
            "proposer_kind": "CONGRESSMAN",
            "brief_summary": None,
            "gpt_summary": None,
            "propose_date": "2026-04-19",
            "stage": "접수",
        }
    ]

    with (
        patch(
            "lawdigest_ai.processor.manual_summary_repair_service.get_db_connection",
            return_value=_mock_connection(rows),
        ),
        patch(
            "lawdigest_ai.processor.manual_summary_repair_service.summarize_bills_with_provider",
            return_value=[
                {
                    "bill_id": "B001",
                    "brief_summary": "요약1",
                    "gpt_summary": "상세1",
                    "summary_tags": '["a","b","c","d","e"]',
                    "error": None,
                }
            ],
        ),
        patch("lawdigest_ai.processor.manual_summary_repair_service.update_bill_summary") as mock_update,
    ):
        report = run_manual_summary_repair(
            mode="test",
            output_path="/tmp/manual-summary-repair.json",
            batch_size=5,
            provider="openai",
            model="gpt-4o-mini",
        )

    assert report["stats"]["db_upserted_count"] == 1
    mock_update.assert_called_once_with(
        bill_id="B001",
        brief_summary="요약1",
        gpt_summary="상세1",
        summary_tags='["a","b","c","d","e"]',
        mode="test",
    )
