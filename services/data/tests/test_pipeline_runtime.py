from __future__ import annotations

import json
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


def test_bill_agent_report_delegates_to_agentic_report_runtime(tmp_path):
    from lawdigest_data.runtime.pipeline import PipelineRuntime

    with patch(
        "lawdigest_ai.processor.agentic_bill_report.run_agentic_bill_reports",
        return_value={"stats": {"success_count": 1}},
    ) as run_reports:
        result = PipelineRuntime(log_dir=tmp_path).run_bill_agent_report(
            mode="dry_run",
            limit=1,
            output_dir="/tmp/reports",
            read_mode="prod",
        )

    run_reports.assert_called_once_with(
        mode="dry_run",
        limit=1,
        output_dir="/tmp/reports",
        read_mode="prod",
        codex_model=None,
        stop_on_error=False,
        target="passed",
        concurrency=1,
        inspection=False,
    )
    assert result["command"] == "bill.agent_report"
    assert result["steps"][0]["step"] == "generate_passed_bill_reports"
    assert result["status"] == "success"


def test_bill_agent_report_can_target_all_bills(tmp_path):
    from lawdigest_data.runtime.pipeline import PipelineRuntime

    with patch(
        "lawdigest_ai.processor.agentic_bill_report.run_agentic_bill_reports",
        return_value={"stats": {"success_count": 1}},
    ) as run_reports:
        result = PipelineRuntime(log_dir=tmp_path).run_bill_agent_report(
            mode="dry_run",
            limit=1,
            output_dir="/tmp/reports",
            read_mode="prod",
            target="all",
        )

    run_reports.assert_called_once_with(
        mode="dry_run",
        limit=1,
        output_dir="/tmp/reports",
        read_mode="prod",
        codex_model=None,
        stop_on_error=False,
        target="all",
        concurrency=1,
        inspection=False,
    )
    assert result["steps"][0]["step"] == "generate_all_bill_reports"


def test_bill_agent_report_forwards_usage_meter_snapshot(tmp_path):
    from lawdigest_data.runtime.pipeline import PipelineRuntime

    with patch(
        "lawdigest_ai.processor.agentic_bill_report.run_agentic_bill_reports",
        return_value={"stats": {"success_count": 1}},
    ) as run_reports:
        PipelineRuntime(log_dir=tmp_path).run_bill_agent_report(
            mode="dry_run",
            limit=1,
            output_dir="/tmp/reports",
            weekly_usage_before=41.2,
            weekly_usage_after=40.7,
            five_hour_usage_before=8.0,
            five_hour_usage_after=9.5,
        )

    run_reports.assert_called_once_with(
        mode="dry_run",
        limit=1,
        output_dir="/tmp/reports",
        read_mode=None,
        codex_model=None,
        stop_on_error=False,
        target="passed",
        concurrency=1,
        inspection=False,
        usage_meter={
            "weekly": {"before_percent": 41.2, "after_percent": 40.7},
            "five_hour": {"before_percent": 8.0, "after_percent": 9.5},
        },
    )


def test_bill_agent_report_forwards_inspection_mode(tmp_path):
    from lawdigest_data.runtime.pipeline import PipelineRuntime

    with patch(
        "lawdigest_ai.processor.agentic_bill_report.run_agentic_bill_reports",
        return_value={"stats": {"success_count": 1}},
    ) as run_reports:
        PipelineRuntime(log_dir=tmp_path).run_bill_agent_report(
            mode="dry_run",
            limit=3,
            output_dir="/tmp/reports",
            read_mode="prod",
            inspection=True,
        )

    run_reports.assert_called_once_with(
        mode="dry_run",
        limit=3,
        output_dir="/tmp/reports",
        read_mode="prod",
        codex_model=None,
        stop_on_error=False,
        target="passed",
        concurrency=1,
        inspection=True,
    )


def test_bill_agent_report_fails_when_all_agent_reports_fail(tmp_path):
    from lawdigest_data.runtime.pipeline import PipelineRuntime

    with patch(
        "lawdigest_ai.processor.agentic_bill_report.run_agentic_bill_reports",
        return_value={
            "stats": {
                "target_count": 1,
                "processed_count": 1,
                "success_count": 0,
                "failure_count": 1,
            }
        },
    ):
        try:
            PipelineRuntime(log_dir=tmp_path).run_bill_agent_report(mode="dry_run", limit=1)
        except RuntimeError as exc:
            assert "모든 법안 리포트 생성에 실패" in str(exc)
        else:
            raise AssertionError("모든 리포트가 실패했는데 파이프라인이 성공하면 안 됩니다.")


def test_bill_search_rebuild_delegates_to_search_document_service(tmp_path):
    from lawdigest_data.runtime.pipeline import PipelineRuntime

    manager = MagicMock()
    manager.rebuild_bill_search_documents.return_value = {"rebuilt": 3}

    with patch("lawdigest_data.runtime.pipeline._build_workflow_manager", return_value=manager):
        result = PipelineRuntime(log_dir=tmp_path).run_bill_search_rebuild(mode="dry_run", limit=3)

    manager.rebuild_bill_search_documents.assert_called_once_with(limit=3)
    assert result["command"] == "bill.search_rebuild"
    assert result["steps"][0]["step"] == "rebuild_bill_search_documents"
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


def test_cli_dispatches_ai_summary_with_codex_default(tmp_path):
    from lawdigest_data.runtime.cli import main

    with patch("lawdigest_data.runtime.cli.PipelineRuntime") as Runtime:
        Runtime.return_value.run_ai_summary.return_value = {"status": "success"}
        exit_code = main([
            "--log-dir",
            str(tmp_path),
            "ai-summary",
            "--mode",
            "dry_run",
            "--limit",
            "1",
            "--batch-size",
            "1",
        ])

    assert exit_code == 0
    Runtime.return_value.run_ai_summary.assert_called_once_with(
        mode="dry_run",
        cli_provider="codex",
        limit=1,
        batch_size=1,
        output_path="/tmp/lawdigest_ai_summary_results.json",
        stop_on_error=False,
        read_mode=None,
        target_mode="missing",
    )


def test_cli_dispatches_bill_agent_report(tmp_path):
    from lawdigest_data.runtime.cli import main

    with patch("lawdigest_data.runtime.cli.PipelineRuntime") as Runtime:
        Runtime.return_value.run_bill_agent_report.return_value = {"status": "success"}
        exit_code = main([
            "--log-dir",
            str(tmp_path),
            "bill-agent-report",
            "--mode",
            "dry_run",
            "--limit",
            "1",
            "--output-dir",
            "/tmp/reports",
            "--read-mode",
            "prod",
        ])

    assert exit_code == 0
    Runtime.return_value.run_bill_agent_report.assert_called_once_with(
        mode="dry_run",
        limit=1,
        output_dir="/tmp/reports",
        read_mode="prod",
        codex_model=None,
        stop_on_error=False,
        target="passed",
        concurrency=1,
        weekly_usage_before=None,
        weekly_usage_after=None,
        five_hour_usage_before=None,
        five_hour_usage_after=None,
        inspection=False,
    )


def test_cli_dispatches_bill_search_rebuild(tmp_path):
    from lawdigest_data.runtime.cli import main

    with patch("lawdigest_data.runtime.cli.PipelineRuntime") as Runtime:
        Runtime.return_value.run_bill_search_rebuild.return_value = {"status": "success"}
        exit_code = main([
            "--log-dir",
            str(tmp_path),
            "bill-search-rebuild",
            "--mode",
            "dry_run",
            "--limit",
            "25",
        ])

    assert exit_code == 0
    Runtime.return_value.run_bill_search_rebuild.assert_called_once_with(
        mode="dry_run",
        limit=25,
    )


def test_cli_dispatches_bill_agent_report_target_all(tmp_path):
    from lawdigest_data.runtime.cli import main

    with patch("lawdigest_data.runtime.cli.PipelineRuntime") as Runtime:
        Runtime.return_value.run_bill_agent_report.return_value = {"status": "success"}
        exit_code = main([
            "--log-dir",
            str(tmp_path),
            "bill-agent-report",
            "--mode",
            "dry_run",
            "--limit",
            "1",
            "--output-dir",
            "/tmp/reports",
            "--read-mode",
            "prod",
            "--target",
            "all",
        ])

    assert exit_code == 0
    Runtime.return_value.run_bill_agent_report.assert_called_once_with(
        mode="dry_run",
        limit=1,
        output_dir="/tmp/reports",
        read_mode="prod",
        codex_model=None,
        stop_on_error=False,
        target="all",
        concurrency=1,
        weekly_usage_before=None,
        weekly_usage_after=None,
        five_hour_usage_before=None,
        five_hour_usage_after=None,
        inspection=False,
    )


def test_cli_dispatches_bill_agent_report_usage_meter(tmp_path):
    from lawdigest_data.runtime.cli import main

    with patch("lawdigest_data.runtime.cli.PipelineRuntime") as Runtime:
        Runtime.return_value.run_bill_agent_report.return_value = {"status": "success"}
        exit_code = main([
            "--log-dir",
            str(tmp_path),
            "bill-agent-report",
            "--mode",
            "dry_run",
            "--limit",
            "1",
            "--weekly-usage-before",
            "41.2",
            "--weekly-usage-after",
            "40.7",
            "--five-hour-usage-before",
            "8",
            "--five-hour-usage-after",
            "9.5",
        ])

    assert exit_code == 0
    Runtime.return_value.run_bill_agent_report.assert_called_once_with(
        mode="dry_run",
        limit=1,
        output_dir="/tmp/lawdigest-bill-agent-reports",
        read_mode=None,
        codex_model=None,
        stop_on_error=False,
        target="passed",
        concurrency=1,
        weekly_usage_before=41.2,
        weekly_usage_after=40.7,
        five_hour_usage_before=8.0,
        five_hour_usage_after=9.5,
        inspection=False,
    )


def test_cli_dispatches_bill_agent_report_concurrency(tmp_path):
    from lawdigest_data.runtime.cli import main

    with patch("lawdigest_data.runtime.cli.PipelineRuntime") as Runtime:
        Runtime.return_value.run_bill_agent_report.return_value = {"status": "success"}
        exit_code = main([
            "--log-dir",
            str(tmp_path),
            "bill-agent-report",
            "--mode",
            "dry_run",
            "--limit",
            "2",
            "--concurrency",
            "3",
        ])

    assert exit_code == 0
    Runtime.return_value.run_bill_agent_report.assert_called_once_with(
        mode="dry_run",
        limit=2,
        output_dir="/tmp/lawdigest-bill-agent-reports",
        read_mode=None,
        codex_model=None,
        stop_on_error=False,
        target="passed",
        concurrency=3,
        weekly_usage_before=None,
        weekly_usage_after=None,
        five_hour_usage_before=None,
        five_hour_usage_after=None,
        inspection=False,
    )


def test_cli_dispatches_bill_agent_report_inspection(tmp_path):
    from lawdigest_data.runtime.cli import main

    with patch("lawdigest_data.runtime.cli.PipelineRuntime") as Runtime:
        Runtime.return_value.run_bill_agent_report.return_value = {"status": "success"}
        exit_code = main([
            "--log-dir",
            str(tmp_path),
            "bill-agent-report",
            "--mode",
            "dry_run",
            "--limit",
            "3",
            "--inspection",
        ])

    assert exit_code == 0
    Runtime.return_value.run_bill_agent_report.assert_called_once_with(
        mode="dry_run",
        limit=3,
        output_dir="/tmp/lawdigest-bill-agent-reports",
        read_mode=None,
        codex_model=None,
        stop_on_error=False,
        target="passed",
        concurrency=1,
        weekly_usage_before=None,
        weekly_usage_after=None,
        five_hour_usage_before=None,
        five_hour_usage_after=None,
        inspection=True,
    )
