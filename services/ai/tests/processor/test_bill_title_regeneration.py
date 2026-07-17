import hashlib
import json
import threading
from unittest.mock import MagicMock, patch

import pytest


def _target(**overrides):
    row = {
        "bill_id": "B001",
        "bill_name": "테스트법률안",
        "title": "현행법은 오래된 제도를 규정하고 있음.",
        "summary": "제안이유 및 주요내용\n\n현행법은 오래된 제도를 규정하고 있음. 이에 새 제도를 도입하려는 것임.",
        "gpt_summary": "## 쉬운 요약\n- 새 제도를 도입해요.\n\n## 주요 내용\n**제도 개선**: 절차를 바꿔요.",
        "propose_date": "2026-07-16",
    }
    row.update(overrides)
    return row


def test_is_raw_summary_copy_title_matches_exact_investigation_contract():
    from lawdigest_ai.processor.bill_title_regeneration import is_raw_summary_copy_title

    assert is_raw_summary_copy_title(_target()) is True
    assert is_raw_summary_copy_title(_target(title="새 제도 도입을 위한 테스트법률안")) is False
    assert is_raw_summary_copy_title(_target(gpt_summary="일반 요약")) is False


@pytest.mark.parametrize("heading", ["제안이유", "주요내용"])
def test_is_raw_summary_copy_title_accepts_single_section_heading(heading):
    from lawdigest_ai.processor.bill_title_regeneration import is_raw_summary_copy_title

    assert is_raw_summary_copy_title(
        _target(
            summary=f"{heading}\n\n현행법은 오래된 제도를 규정하고 있음. 이에 새 제도를 도입하려는 것임."
        )
    ) is True


def test_fetch_bill_title_regeneration_targets_filters_before_limit():
    from lawdigest_ai.processor.bill_title_regeneration import fetch_bill_title_regeneration_targets

    conn = MagicMock()
    cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchall.return_value = [
        _target(bill_id="NOT_TARGET", title="새 제도 도입을 위한 테스트법률안"),
        _target(bill_id="B001"),
        _target(bill_id="B002"),
    ]

    with patch(
        "lawdigest_ai.processor.bill_title_regeneration.get_db_connection",
        return_value=conn,
    ):
        targets = fetch_bill_title_regeneration_targets(mode="dry_run", read_mode="prod", limit=1)

    query, params = cur.execute.call_args.args
    assert "gpt_summary LIKE %s" in query
    assert "ORDER BY propose_date DESC, bill_id DESC" in query
    assert params == ("%## 쉬운 요약%", "%## 주요 내용%")
    assert [row["bill_id"] for row in targets] == ["B001"]


def test_build_bill_title_batch_prompt_only_requests_titles():
    from lawdigest_ai.processor.bill_title_regeneration import build_bill_title_batch_prompt

    prompt = build_bill_title_batch_prompt([_target()])

    assert "제목만 생성" in prompt
    assert "기존 리포트 본문을 수정하거나 다시 작성하지 마세요" in prompt
    assert '"bill_id": "B001"' in prompt
    assert '"bill_name": "테스트법률안"' in prompt
    assert "새 제도를 도입해요" in prompt
    assert '"titles"' in prompt
    assert '"report_body"' not in prompt


def test_bill_title_regeneration_keeps_low_cost_default_model():
    from lawdigest_ai.processor.bill_title_regeneration import (
        DEFAULT_TITLE_CODEX_MODEL,
        CodexBillTitleAgent,
    )

    assert DEFAULT_TITLE_CODEX_MODEL == "gpt-5.4-mini"
    assert CodexBillTitleAgent().model == "gpt-5.4-mini"


def test_parse_bill_title_batch_output_validates_ids_and_title_contract():
    from lawdigest_ai.processor.bill_title_regeneration import parse_bill_title_batch_output

    parsed = parse_bill_title_batch_output(
        json.dumps(
            {
                "titles": [
                    {
                        "bill_id": "B001",
                        "title": "새 제도 도입을 위한 테스트법률안",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        [_target()],
    )

    assert parsed == {"B001": "새 제도 도입을 위한 테스트법률안"}


@pytest.mark.parametrize(
    "payload",
    [
        {"titles": []},
        {
            "titles": [
                {"bill_id": "OTHER", "title": "새 제도 도입을 위한 테스트법률안"}
            ]
        },
        {
            "titles": [
                {"bill_id": "B001", "title": "현행법은 오래된 제도를 규정하고 있음."}
            ]
        },
    ],
)
def test_parse_bill_title_batch_output_rejects_missing_wrong_or_invalid_titles(payload):
    from lawdigest_ai.processor.bill_title_regeneration import parse_bill_title_batch_output

    with pytest.raises(RuntimeError):
        parse_bill_title_batch_output(json.dumps(payload, ensure_ascii=False), [_target()])


def test_codex_bill_title_agent_sends_title_only_prompt_and_parses_output(tmp_path):
    from lawdigest_ai.processor.bill_title_regeneration import CodexBillTitleAgent

    output_path = tmp_path / "titles.json"
    report_agent = MagicMock()
    report_agent.build_command.return_value = (["codex", "exec"], "TITLE_ONLY_PROMPT")
    report_agent.build_environment.return_value = {"CODEX_HOME": "/tmp/codex"}
    report_agent.workdir = "/tmp"
    report_agent.timeout_seconds = 30

    def run_codex(*args, **kwargs):
        output_path.write_text(
            json.dumps(
                {
                    "titles": [
                        {"bill_id": "B001", "title": "새 제도 도입을 위한 테스트법률안"}
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return MagicMock(returncode=0, stdout="", stderr="")

    with patch(
        "lawdigest_ai.processor.bill_title_regeneration.CodexBillReportAgent",
        return_value=report_agent,
    ), patch(
        "lawdigest_ai.processor.bill_title_regeneration.subprocess.run",
        side_effect=run_codex,
    ) as subprocess_run:
        generated = CodexBillTitleAgent().write_titles_batch(
            [_target()],
            output_path=str(output_path),
        )

    prompt = report_agent.build_command.call_args.kwargs["prompt"]
    assert "제목만 생성" in prompt
    assert generated == {"B001": "새 제도 도입을 위한 테스트법률안"}
    subprocess_run.assert_called_once_with(
        ["codex", "exec"],
        input="TITLE_ONLY_PROMPT",
        capture_output=True,
        text=True,
        cwd="/tmp",
        env={"CODEX_HOME": "/tmp/codex"},
        timeout=30,
    )


def test_run_bill_title_regeneration_updates_only_title_and_writes_result(tmp_path):
    from lawdigest_ai.processor.bill_title_regeneration import run_bill_title_regeneration

    target = _target()
    generated = {"B001": "새 제도 도입을 위한 테스트법률안"}
    agent = MagicMock()
    agent.write_titles_batch.return_value = generated

    with patch(
        "lawdigest_ai.processor.bill_title_regeneration.fetch_bill_title_regeneration_targets",
        return_value=[target],
    ), patch(
        "lawdigest_ai.processor.bill_title_regeneration.update_bill_title_if_current",
        return_value=True,
    ) as update_title:
        result = run_bill_title_regeneration(
            mode="prod",
            limit=1,
            output_dir=str(tmp_path),
            agent=agent,
        )

    update_title.assert_called_once_with(
        bill_id="B001",
        title="새 제도 도입을 위한 테스트법률안",
        expected_title=target["title"],
        mode="prod",
    )
    assert result["status"] == "success"
    assert result["model"] == "gpt-5.4-mini"
    assert result["stats"] == {"target_count": 1, "success_count": 1, "failure_count": 0}
    assert result["items"][0]["gpt_summary_sha256"] == hashlib.sha256(
        target["gpt_summary"].encode("utf-8")
    ).hexdigest()
    assert (tmp_path / "result.json").exists()


def test_run_bill_title_regeneration_dry_run_does_not_update_db(tmp_path):
    from lawdigest_ai.processor.bill_title_regeneration import run_bill_title_regeneration

    agent = MagicMock()
    agent.write_titles_batch.return_value = {"B001": "새 제도 도입을 위한 테스트법률안"}

    with patch(
        "lawdigest_ai.processor.bill_title_regeneration.fetch_bill_title_regeneration_targets",
        return_value=[_target()],
    ), patch(
        "lawdigest_ai.processor.bill_title_regeneration.update_bill_title_if_current",
    ) as update_title:
        result = run_bill_title_regeneration(
            mode="dry_run",
            read_mode="prod",
            limit=1,
            output_dir=str(tmp_path),
            agent=agent,
        )

    update_title.assert_not_called()
    assert result["items"][0]["db_updated"] is False


def test_run_bill_title_regeneration_runs_batches_concurrently_and_preserves_order(tmp_path):
    from lawdigest_ai.processor.bill_title_regeneration import run_bill_title_regeneration

    targets = [_target(bill_id=f"B{index:03d}") for index in range(10)]
    barrier = threading.Barrier(2)
    agent = MagicMock()

    def generate(batch, *, output_path):
        barrier.wait(timeout=2)
        return {
            bill["bill_id"]: f"새 제도 도입을 위한 {bill['bill_name']}"
            for bill in batch
        }

    agent.write_titles_batch.side_effect = generate
    with patch(
        "lawdigest_ai.processor.bill_title_regeneration.fetch_bill_title_regeneration_targets",
        return_value=targets,
    ):
        result = run_bill_title_regeneration(
            mode="dry_run",
            limit=10,
            output_dir=str(tmp_path),
            concurrency=2,
            agent=agent,
        )

    assert result["concurrency"] == 2
    assert [item["bill_id"] for item in result["items"]] == [
        target["bill_id"] for target in targets
    ]
