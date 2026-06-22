from __future__ import annotations

import json
import os
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List

DEFAULT_LOG_DIR = Path(os.getenv("LAWDIGEST_PIPELINE_LOG_DIR", "/tmp/lawdigest-pipeline"))


def _build_workflow_manager(mode: str):
    from lawdigest_data.core.WorkFlowManager import WorkFlowManager

    return WorkFlowManager(mode)


def _build_usage_meter_snapshot(
    *,
    weekly_usage_before: float | None,
    weekly_usage_after: float | None,
    five_hour_usage_before: float | None,
    five_hour_usage_after: float | None,
) -> dict[str, Any] | None:
    usage_meter: dict[str, Any] = {}
    weekly = {
        "before_percent": weekly_usage_before,
        "after_percent": weekly_usage_after,
    }
    five_hour = {
        "before_percent": five_hour_usage_before,
        "after_percent": five_hour_usage_after,
    }
    if any(value is not None for value in weekly.values()):
        usage_meter["weekly"] = {key: value for key, value in weekly.items() if value is not None}
    if any(value is not None for value in five_hour.values()):
        usage_meter["five_hour"] = {key: value for key, value in five_hour.items() if value is not None}
    return usage_meter or None


class PipelineRunRecorder:
    """Append-only JSONL recorder for pipeline run state."""

    def __init__(self, log_dir: str | Path | None = None):
        self.log_dir = Path(log_dir) if log_dir else DEFAULT_LOG_DIR
        self.log_path = self.log_dir / "pipeline-runs.jsonl"

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _append(self, payload: Dict[str, Any]) -> None:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")

    def start(self, command: str, params: Dict[str, Any]) -> str:
        run_id = str(uuid.uuid4())
        self._append({
            "event": "run_started",
            "run_id": run_id,
            "command": command,
            "params": params,
            "timestamp": self._now(),
        })
        return run_id

    def step(self, run_id: str, step: str, status: str, result: Dict[str, Any] | None = None) -> None:
        self._append({
            "event": "step_finished",
            "run_id": run_id,
            "step": step,
            "status": status,
            "result": result or {},
            "timestamp": self._now(),
        })

    def finish(self, run_id: str, status: str, result: Dict[str, Any] | None = None) -> None:
        self._append({
            "event": "run_finished",
            "run_id": run_id,
            "status": status,
            "result": result or {},
            "timestamp": self._now(),
        })


class PipelineRuntime:
    def __init__(self, log_dir: str | Path | None = None):
        self.recorder = PipelineRunRecorder(log_dir)

    def _run(
        self,
        command: str,
        params: Dict[str, Any],
        executor: Callable[[str], List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        run_id = self.recorder.start(command, params)
        try:
            steps = executor(run_id)
            result = {"run_id": run_id, "command": command, "status": "success", "steps": steps}
            self.recorder.finish(run_id, "success", result)
            return result
        except Exception as exc:
            result = {
                "run_id": run_id,
                "command": command,
                "status": "failed",
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }
            self.recorder.finish(run_id, "failed", result)
            raise

    def _record_step(
        self,
        run_id: str,
        steps: List[Dict[str, Any]],
        step: str,
        result: Dict[str, Any],
    ) -> Dict[str, Any]:
        entry = {"step": step, "result": result}
        steps.append(entry)
        self.recorder.step(run_id, step, "success", result)
        return result

    def run_bill_ingest(
        self,
        *,
        mode: str = "dry_run",
        start_date: str | None = None,
        end_date: str | None = None,
        age: str | None = "22",
    ) -> Dict[str, Any]:
        params = {"mode": mode, "start_date": start_date, "end_date": end_date, "age": age}

        def execute(run_id: str) -> List[Dict[str, Any]]:
            manager = _build_workflow_manager(mode)
            steps: List[Dict[str, Any]] = []
            fetched = self._record_step(
                run_id,
                steps,
                "fetch_bills",
                manager.fetch_bills_data_step(start_date=start_date, end_date=end_date, age=age),
            )
            fetched_artifact = fetched.get("artifact_path")
            if not fetched_artifact:
                self._record_step(run_id, steps, "skip", {"reason": "fetch_bills produced no artifact"})
                return steps

            processed = self._record_step(
                run_id,
                steps,
                "process_bills",
                manager.process_bills_data_step(fetched_artifact),
            )
            processed_artifact = processed.get("artifact_path")
            if not processed_artifact:
                self._record_step(run_id, steps, "skip", {"reason": "process_bills produced no artifact"})
                return steps

            self._record_step(run_id, steps, "upsert_bills", manager.upsert_bills_data_step(processed_artifact))
            return steps

        return self._run("bill.ingest", params, execute)

    def run_bill_status_sync(
        self,
        *,
        mode: str = "dry_run",
        start_date: str | None = None,
        end_date: str | None = None,
        age: str | None = "22",
    ) -> Dict[str, Any]:
        params = {"mode": mode, "start_date": start_date, "end_date": end_date, "age": age}

        def execute(run_id: str) -> List[Dict[str, Any]]:
            manager = _build_workflow_manager(mode)
            steps: List[Dict[str, Any]] = []
            self._record_step(run_id, steps, "update_lawmakers", manager.update_lawmakers_data())
            for fetch_name, upsert_name in (
                ("fetch_lifecycle_step", "upsert_lifecycle_step"),
                ("fetch_vote_step", "upsert_vote_step"),
            ):
                fetched = self._record_step(
                    run_id,
                    steps,
                    fetch_name,
                    getattr(manager, fetch_name)(start_date=start_date, end_date=end_date, age=age),
                )
                artifact_path = fetched.get("artifact_path")
                if artifact_path:
                    self._record_step(run_id, steps, upsert_name, getattr(manager, upsert_name)(artifact_path))
                else:
                    self._record_step(run_id, steps, f"skip_{upsert_name}", {"reason": "no artifact"})
            return steps

        return self._run("bill.status_sync", params, execute)

    def run_ai_batch_submit(
        self,
        *,
        mode: str = "dry_run",
        provider: str = "openai",
        limit: int = 200,
        model: str | None = None,
    ) -> Dict[str, Any]:
        params = {"mode": mode, "provider": provider, "limit": limit, "model": model}

        def execute(run_id: str) -> List[Dict[str, Any]]:
            from lawdigest_ai.processor.batch_submit import submit_batch

            steps: List[Dict[str, Any]] = []
            self._record_step(
                run_id,
                steps,
                "submit_batch",
                submit_batch(limit=limit, model=model, mode=mode, provider=provider),
            )
            return steps

        return self._run("ai.batch_submit", params, execute)

    def run_ai_batch_ingest(
        self,
        *,
        mode: str = "dry_run",
        provider: str = "all",
        max_jobs: int = 10,
    ) -> Dict[str, Any]:
        params = {"mode": mode, "provider": provider, "max_jobs": max_jobs}

        def execute(run_id: str) -> List[Dict[str, Any]]:
            from lawdigest_ai.processor.batch_ingest import ingest_batch_results

            steps: List[Dict[str, Any]] = []
            self._record_step(
                run_id,
                steps,
                "ingest_batch_results",
                ingest_batch_results(max_jobs=max_jobs, mode=mode, provider=provider),
            )
            return steps

        return self._run("ai.batch_ingest", params, execute)

    def run_ai_native_repair(
        self,
        *,
        mode: str = "dry_run",
        provider: str = "openai",
        limit: int = 200,
        batch_size: int = 10,
        model: str | None = None,
        output_path: str = "/tmp/lawdigest_missing_summaries.json",
    ) -> Dict[str, Any]:
        params = {
            "mode": mode,
            "provider": provider,
            "limit": limit,
            "batch_size": batch_size,
            "model": model,
            "output_path": output_path,
        }

        def execute(run_id: str) -> List[Dict[str, Any]]:
            from lawdigest_ai.processor.manual_summary_repair_service import run_manual_summary_repair

            steps: List[Dict[str, Any]] = []
            self._record_step(
                run_id,
                steps,
                "repair_native_summary",
                run_manual_summary_repair(
                    mode=mode,
                    output_path=output_path,
                    batch_size=batch_size,
                    limit=limit,
                    provider=provider,
                    model=model,
                ),
            )
            return steps

        return self._run("ai.native_repair", params, execute)

    def _run_ai_cli_summary(
        self,
        *,
        command: str,
        step: str,
        mode: str = "dry_run",
        cli_provider: str = "gemini",
        limit: int = 20,
        batch_size: int = 5,
        output_path: str = "/tmp/gemini_ai_summary_results.json",
        stop_on_error: bool = False,
        read_mode: str | None = None,
        target_mode: str = "missing",
    ) -> Dict[str, Any]:
        params = {
            "mode": mode,
            "cli_provider": cli_provider,
            "limit": limit,
            "batch_size": batch_size,
            "output_path": output_path,
            "stop_on_error": stop_on_error,
            "read_mode": read_mode,
            "target_mode": target_mode,
        }

        def execute(run_id: str) -> List[Dict[str, Any]]:
            from lawdigest_ai.processor.gemini_repair_pipeline import run_gemini_repair_pipeline

            steps: List[Dict[str, Any]] = []
            self._record_step(
                run_id,
                steps,
                step,
                run_gemini_repair_pipeline(
                    mode=mode,
                    limit=limit,
                    batch_size=batch_size,
                    output_path=output_path,
                    stop_on_error=stop_on_error,
                    read_mode=read_mode,
                    target_mode=target_mode,
                    cli_provider=cli_provider,
                ),
            )
            return steps

        return self._run(command, params, execute)

    def run_ai_summary(
        self,
        *,
        mode: str = "dry_run",
        cli_provider: str = "gemini",
        limit: int = 20,
        batch_size: int = 5,
        output_path: str = "/tmp/gemini_ai_summary_results.json",
        stop_on_error: bool = False,
        read_mode: str | None = None,
        target_mode: str = "missing",
    ) -> Dict[str, Any]:
        return self._run_ai_cli_summary(
            command="ai.summary",
            step="summarize_cli_realtime",
            mode=mode,
            cli_provider=cli_provider,
            limit=limit,
            batch_size=batch_size,
            output_path=output_path,
            stop_on_error=stop_on_error,
            read_mode=read_mode,
            target_mode=target_mode,
        )

    def run_ai_cli_repair(
        self,
        *,
        mode: str = "dry_run",
        cli_provider: str = "gemini",
        limit: int = 20,
        batch_size: int = 5,
        output_path: str = "/tmp/gemini_ai_summary_results.json",
        stop_on_error: bool = False,
        read_mode: str | None = None,
        target_mode: str = "missing",
    ) -> Dict[str, Any]:
        return self._run_ai_cli_summary(
            command="ai.cli_repair",
            step="repair_cli_summary",
            mode=mode,
            cli_provider=cli_provider,
            limit=limit,
            batch_size=batch_size,
            output_path=output_path,
            stop_on_error=stop_on_error,
            read_mode=read_mode,
            target_mode=target_mode,
        )

    def run_bill_agent_report(
        self,
        *,
        mode: str = "dry_run",
        limit: int = 5,
        output_dir: str = "/tmp/lawdigest-bill-agent-reports",
        read_mode: str | None = None,
        codex_model: str | None = None,
        stop_on_error: bool = False,
        target: str = "passed",
        concurrency: int = 1,
        weekly_usage_before: float | None = None,
        weekly_usage_after: float | None = None,
        five_hour_usage_before: float | None = None,
        five_hour_usage_after: float | None = None,
    ) -> Dict[str, Any]:
        usage_meter = _build_usage_meter_snapshot(
            weekly_usage_before=weekly_usage_before,
            weekly_usage_after=weekly_usage_after,
            five_hour_usage_before=five_hour_usage_before,
            five_hour_usage_after=five_hour_usage_after,
        )
        params = {
            "mode": mode,
            "limit": limit,
            "output_dir": output_dir,
            "read_mode": read_mode,
            "codex_model": codex_model,
            "stop_on_error": stop_on_error,
            "target": target,
            "concurrency": concurrency,
            "usage_meter": usage_meter,
        }

        def execute(run_id: str) -> List[Dict[str, Any]]:
            from lawdigest_ai.processor.agentic_bill_report import run_agentic_bill_reports

            steps: List[Dict[str, Any]] = []
            report_kwargs = {
                "mode": mode,
                "limit": limit,
                "output_dir": output_dir,
                "read_mode": read_mode,
                "codex_model": codex_model,
                "stop_on_error": stop_on_error,
                "target": target,
                "concurrency": concurrency,
            }
            if usage_meter is not None:
                report_kwargs["usage_meter"] = usage_meter
            report = run_agentic_bill_reports(
                **report_kwargs,
            )
            self._record_step(
                run_id,
                steps,
                "generate_all_bill_reports" if target == "all" else "generate_passed_bill_reports",
                report,
            )
            stats = report.get("stats", {})
            if stats.get("target_count", 0) > 0 and stats.get("success_count", 0) == 0:
                raise RuntimeError("모든 법안 리포트 생성에 실패했습니다.")
            return steps

        return self._run("bill.agent_report", params, execute)
