import json
from pathlib import Path
from unittest.mock import patch

import pytest


REPORT_BODY = (
    "# 청문 절차 정비법안\n\n"
    "## 쉬운 요약\n**청문 절차**가 더 분명해져요. <mark>의견을 말할 기회를 분명히 해요.</mark>\n\n"
    "## 주요 내용\n- **절차 정비**: 청문 절차를 정비해요.\n\n"
    "## 무엇이 달라지나\n\n"
    "### 1) 의견 확인 절차 정비\n\n"
    "처분 전에 청문 절차를 거치도록 해요.\n\n"
    "- 당사자가 의견을 직접 말할 수 있어요.\n"
)


def test_bill_tooltip_prompt_only_requests_context_decisions():
    from lawdigest_ai.processor.agentic_bill_tooltip import build_bill_tooltip_prompt
    from lawdigest_ai.processor.legal_term_glossary import LegalTermEntry

    prompt = build_bill_tooltip_prompt(
        bill={"bill_id": "PRC_TOOLTIP", "bill_name": "청문 절차 정비법안"},
        report_body=REPORT_BODY,
        candidates=[
            LegalTermEntry(
                term="청문",
                aliases=("청문", "청문 절차"),
                definition="처분 전에 당사자의 의견을 듣는 절차예요.",
            )
        ],
    )

    assert "리포트 본문을 다시 작성하거나 수정하지 마세요" in prompt
    assert '"report_body"' not in prompt.split("출력 스키마:", 1)[1]
    assert '"tooltips"' in prompt
    assert '"relevance":"high"' in prompt
    assert REPORT_BODY in prompt


def test_bill_tooltip_applies_only_high_confidence_high_relevance_exact_surface():
    from lawdigest_ai.processor.agentic_bill_tooltip import apply_tooltip_decisions
    from lawdigest_ai.processor.legal_term_glossary import LegalTermEntry

    candidates = [
        LegalTermEntry(
            term="청문",
            aliases=("청문", "청문 절차"),
            definition="처분 전에 당사자의 의견을 듣는 절차예요.",
        )
    ]
    decision = json.dumps(
        {
            "tooltips": [
                {
                    "term": "청문",
                    "surface": "청문 절차",
                    "confidence": "high",
                    "relevance": "high",
                    "reason": "현재 법안의 의견 진술 절차와 같은 개념이에요.",
                },
                {
                    "term": "청문",
                    "surface": "청문 절차 확대",
                    "confidence": "high",
                    "relevance": "high",
                    "reason": "후보보다 넓은 표현이에요.",
                },
            ],
            "rejected": [],
        },
        ensure_ascii=False,
    )

    rendered, details = apply_tooltip_decisions(REPORT_BODY, candidates, decision)

    assert details["applied_count"] == 1
    assert "{{청문 절차:처분 전에 당사자의 의견을 듣는 절차예요.}}" in rendered
    assert "{{청문 절차 확대:" not in rendered


def test_source_manifest_uses_only_successful_report_items(tmp_path):
    from lawdigest_ai.processor.agentic_bill_tooltip import load_source_manifest_items

    first_report = tmp_path / "BILL_1.md"
    first_report.write_text(REPORT_BODY, encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "items": [
                    {"bill_id": "BILL_1", "bill_name": "청문 절차 정비법안", "status": "success", "report_path": str(first_report)},
                    {"bill_id": "BILL_2", "bill_name": "실패 법안", "status": "failed", "report_path": str(tmp_path / "BILL_2.md")},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    items = load_source_manifest_items(str(manifest_path))

    assert [item["bill_id"] for item in items] == ["BILL_1"]
    assert items[0]["report_body"] == REPORT_BODY


def test_source_manifest_write_mode_fails_when_db_metadata_is_unavailable(tmp_path):
    from lawdigest_ai.processor.agentic_bill_tooltip import fetch_bill_tooltip_targets

    report_path = tmp_path / "BILL_1.md"
    report_path.write_text(REPORT_BODY, encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "bill_id": "BILL_1",
                        "bill_name": "청문 절차 정비법안",
                        "status": "success",
                        "report_path": str(report_path),
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with patch(
        "lawdigest_ai.processor.agentic_bill_tooltip._fetch_bill_metadata",
        side_effect=RuntimeError("metadata unavailable"),
    ), pytest.raises(RuntimeError, match="metadata unavailable"):
        fetch_bill_tooltip_targets(
            mode="prod",
            limit=1,
            source_manifest=str(manifest_path),
        )


def test_run_agentic_bill_tooltips_skips_without_candidates_or_model_call(tmp_path):
    from lawdigest_ai.processor.agentic_bill_tooltip import run_agentic_bill_tooltips

    target = {
        "bill_id": "PRC_NO_TERM",
        "bill_name": "용어 없는 법안",
        "report_body": REPORT_BODY.replace("청문 절차", "의견 확인"),
    }

    with patch(
        "lawdigest_ai.processor.agentic_bill_tooltip.fetch_bill_tooltip_targets",
        return_value=[target],
    ), patch(
        "lawdigest_ai.processor.agentic_bill_tooltip.build_legal_term_tooltip_entries",
        return_value=[],
    ), patch("lawdigest_ai.processor.agentic_bill_tooltip.subprocess.run") as run_codex:
        result = run_agentic_bill_tooltips(
            mode="dry_run",
            limit=1,
            output_dir=str(tmp_path),
        )

    run_codex.assert_not_called()
    assert result["stats"]["skipped_count"] == 1
    assert result["stats"]["failure_count"] == 0
    assert result["items"][0]["reason"] == "no_candidates"


def test_run_agentic_bill_tooltips_upserts_only_valid_applied_result(tmp_path):
    from lawdigest_ai.processor.agentic_bill_tooltip import run_agentic_bill_tooltips
    from lawdigest_ai.processor.legal_term_glossary import LegalTermEntry

    target = {
        "bill_id": "PRC_TOOLTIP",
        "bill_name": "청문 절차 정비법안",
        "brief_summary": "기존 제목",
        "summary_tags": '["행정"]',
        "report_body": REPORT_BODY,
    }
    candidates = [
        LegalTermEntry(
            term="청문",
            aliases=("청문", "청문 절차"),
            definition="처분 전에 당사자의 의견을 듣는 절차예요.",
        )
    ]

    def run_codex(command, **kwargs):
        output_path = Path(command[command.index("--output-last-message") + 1])
        output_path.write_text(
            json.dumps(
                {
                    "tooltips": [
                        {
                            "term": "청문",
                            "surface": "청문 절차",
                            "confidence": "high",
                            "relevance": "high",
                            "reason": "본문의 처분 전 의견 진술 절차와 일치해요.",
                        }
                    ],
                    "rejected": [],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return type("Result", (), {"returncode": 0, "stdout": '{"type":"thread.started","thread_id":"tooltip-thread"}', "stderr": ""})()

    with patch(
        "lawdigest_ai.processor.agentic_bill_tooltip.fetch_bill_tooltip_targets",
        return_value=[target],
    ), patch(
        "lawdigest_ai.processor.agentic_bill_tooltip.build_legal_term_tooltip_entries",
        return_value=candidates,
    ), patch(
        "lawdigest_ai.processor.agentic_bill_tooltip.subprocess.run",
        side_effect=run_codex,
    ), patch("lawdigest_ai.processor.agentic_bill_tooltip.update_bill_summary") as update_summary:
        result = run_agentic_bill_tooltips(
            mode="test",
            limit=1,
            output_dir=str(tmp_path),
            inspection=True,
        )

    assert result["stats"]["success_count"] == 1
    assert result["stats"]["db_upserted_count"] == 1
    assert "prompt" not in result["items"][0]
    assert Path(result["items"][0]["inspection_prompt_path"]).exists()
    update_summary.assert_called_once()
    assert "{{청문 절차:" in update_summary.call_args.kwargs["gpt_summary"]
