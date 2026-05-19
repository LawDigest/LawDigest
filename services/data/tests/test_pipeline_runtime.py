from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch


def test_pipeline_recorder_writes_run_events(tmp_path):
    from lawdigest_data.runtime.pipeline import PipelineRunRecorder

    recorder = PipelineRunRecorder(log_dir=tmp_path)
    run_id = recorder.start(command="bill.ingest", params={"mode": "dry_run"})
    recorder.step(run_id, "fetch", "success", {"count": 1})
    recorder.finish(run_id, "success", {"ok": True})

    lines = [json.loads(line) for line in (tmp_path / "pipeline-runs.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [line["event"] for line in lines] == ["run_started", "step_finished", "run_finished"]
    assert lines[0]["run_id"] == run_id
    assert lines[1]["step"] == "fetch"


def test_bill_ingest_runs_without_airflow_xcom(tmp_path):
    from lawdigest_data.runtime.pipeline import PipelineRuntime

    manager = MagicMock()
    manager.fetch_bills_data_step.return_value = {"artifact_path": "/tmp/fetched.json", "count": 2}
    manager.process_bills_data_step.return_value = {"artifact_path": "/tmp/processed.json", "processed": 2}
    manager.upsert_bills_data_step.return_value = {"upserted": 2}

    with patch("lawdigest_data.runtime.pipeline._build_workflow_manager", return_value=manager):
        result = PipelineRuntime(log_dir=tmp_path).run_bill_ingest(
            mode="dry_run",
            start_date="2026-05-01",
            end_date="2026-05-02",
            age="22",
        )

    manager.fetch_bills_data_step.assert_called_once_with(
        start_date="2026-05-01",
        end_date="2026-05-02",
        age="22",
    )
    manager.process_bills_data_step.assert_called_once_with("/tmp/fetched.json")
    manager.upsert_bills_data_step.assert_called_once_with("/tmp/processed.json")
    assert result["status"] == "success"
    assert result["steps"][-1]["result"] == {"upserted": 2}


def test_bill_ingest_skips_downstream_when_fetch_has_no_artifact(tmp_path):
    from lawdigest_data.runtime.pipeline import PipelineRuntime

    manager = MagicMock()
    manager.fetch_bills_data_step.return_value = {"artifact_path": None, "count": 0}

    with patch("lawdigest_data.runtime.pipeline._build_workflow_manager", return_value=manager):
        result = PipelineRuntime(log_dir=tmp_path).run_bill_ingest(mode="dry_run")

    manager.process_bills_data_step.assert_not_called()
    manager.upsert_bills_data_step.assert_not_called()
    assert result["status"] == "success"
    assert result["steps"][-1]["step"] == "skip"


def test_ai_cli_repair_delegates_to_existing_provider_runtime(tmp_path):
    from lawdigest_data.runtime.pipeline import PipelineRuntime

    with patch(
        "lawdigest_ai.processor.gemini_repair_pipeline.run_gemini_repair_pipeline",
        return_value={"stats": {"success_count": 1}},
    ) as run_repair:
        result = PipelineRuntime(log_dir=tmp_path).run_ai_cli_repair(
            mode="dry_run",
            cli_provider="codex",
            limit=1,
            batch_size=1,
            output_path="/tmp/codex.json",
        )

    run_repair.assert_called_once_with(
        mode="dry_run",
        limit=1,
        batch_size=1,
        output_path="/tmp/codex.json",
        stop_on_error=False,
        read_mode=None,
        target_mode="missing",
        cli_provider="codex",
    )
    assert result["status"] == "success"


def test_ai_summary_uses_gemini_cli_realtime_command(tmp_path):
    from lawdigest_data.runtime.pipeline import PipelineRuntime

    with patch(
        "lawdigest_ai.processor.gemini_repair_pipeline.run_gemini_repair_pipeline",
        return_value={"stats": {"success_count": 1}},
    ) as run_repair:
        result = PipelineRuntime(log_dir=tmp_path).run_ai_summary(
            mode="dry_run",
            cli_provider="gemini",
            limit=1,
            batch_size=1,
            output_path="/tmp/gemini.json",
        )

    run_repair.assert_called_once_with(
        mode="dry_run",
        limit=1,
        batch_size=1,
        output_path="/tmp/gemini.json",
        stop_on_error=False,
        read_mode=None,
        target_mode="missing",
        cli_provider="gemini",
    )
    assert result["command"] == "ai.summary"
    assert result["steps"][0]["step"] == "summarize_cli_realtime"
    assert result["status"] == "success"


def test_cli_dispatches_bill_ingest(tmp_path):
    from lawdigest_data.runtime.cli import main

    with patch("lawdigest_data.runtime.cli.PipelineRuntime") as Runtime:
        Runtime.return_value.run_bill_ingest.return_value = {"status": "success"}
        exit_code = main([
            "--log-dir",
            str(tmp_path),
            "bill-ingest",
            "--mode",
            "dry_run",
            "--start-date",
            "2026-05-01",
            "--end-date",
            "2026-05-02",
        ])

    assert exit_code == 0
    Runtime.return_value.run_bill_ingest.assert_called_once_with(
        mode="dry_run",
        start_date="2026-05-01",
        end_date="2026-05-02",
        age="22",
    )


def test_cli_dispatches_ai_summary(tmp_path):
    from lawdigest_data.runtime.cli import main

    with patch("lawdigest_data.runtime.cli.PipelineRuntime") as Runtime:
        Runtime.return_value.run_ai_summary.return_value = {"status": "success"}
        exit_code = main([
            "--log-dir",
            str(tmp_path),
            "ai-summary",
            "--mode",
            "dry_run",
            "--cli-provider",
            "gemini",
            "--limit",
            "1",
            "--batch-size",
            "1",
            "--output-path",
            "/tmp/gemini.json",
        ])

    assert exit_code == 0
    Runtime.return_value.run_ai_summary.assert_called_once_with(
        mode="dry_run",
        cli_provider="gemini",
        limit=1,
        batch_size=1,
        output_path="/tmp/gemini.json",
        stop_on_error=False,
        read_mode=None,
        target_mode="missing",
    )
