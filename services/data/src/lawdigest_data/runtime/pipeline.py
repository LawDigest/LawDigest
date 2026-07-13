from __future__ import annotations

import json
import os
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List

DEFAULT_LOG_DIR = Path(os.getenv("LAWDIGEST_PIPELINE_LOG_DIR", "/tmp/lawdigest-pipeline"))
MAX_AI_SUMMARY_CHUNK_SIZE = 5


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


def _chunk_output_path(output_path: str, chunk_number: int) -> str:
    path = Path(output_path)
    suffix = path.suffix or ".json"
    return str(path.with_name(f"{path.stem}.part{chunk_number:03d}{suffix}"))


def _merge_usage_totals(items: List[Dict[str, Any]]) -> Dict[str, int]:
    totals: Dict[str, int] = {}
    for item in items:
        usage = item.get("stats", {}).get("usage_totals", {})
        if not isinstance(usage, dict):
            continue
        for key, value in usage.items():
            if isinstance(value, int):
                totals[key] = totals.get(key, 0) + value
    return totals


def _write_json_output(payload: Dict[str, Any], output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


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
            status = self._status_from_steps(steps)
            result = {"run_id": run_id, "command": command, "status": status, "steps": steps}
            self.recorder.finish(run_id, status, result)
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

    @staticmethod
    def _status_from_steps(steps: List[Dict[str, Any]]) -> str:
        statuses = {str(step.get("status") or "success") for step in steps}
        if "failed" in statuses:
            return "failed"
        if "partial" in statuses:
            return "partial"
        if "empty" in statuses or "skipped" in statuses:
            return "empty"
        return "success"

    def _record_step(
        self,
        run_id: str,
        steps: List[Dict[str, Any]],
        step: str,
        result: Dict[str, Any],
    ) -> Dict[str, Any]:
        status = str(result.get("status") or "success")
        entry = {"step": step, "status": status, "result": result}
        steps.append(entry)
        self.recorder.step(run_id, step, status, result)
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
                self._record_step(
                    run_id,
                    steps,
                    "skip",
                    {"status": "empty", "reason": "fetch_bills produced no artifact"},
                )
                return steps

            processed = self._record_step(
                run_id,
                steps,
                "process_bills",
                manager.process_bills_data_step(fetched_artifact),
            )
            processed_artifact = processed.get("artifact_path")
            if not processed_artifact:
                self._record_step(
                    run_id,
                    steps,
                    "skip",
                    {"status": "empty", "reason": "process_bills produced no artifact"},
                )
                return steps

            self._record_step(run_id, steps, "upsert_bills", manager.upsert_bills_data_step(processed_artifact))
            return steps

        return self._run("bill.ingest", params, execute)

    def run_bill_ingest_verify(
        self,
        *,
        mode: str = "dry_run",
        limit: int = 100,
    ) -> Dict[str, Any]:
        params = {"mode": mode, "limit": limit}

        def execute(run_id: str) -> List[Dict[str, Any]]:
            manager = _build_workflow_manager(mode)
            steps: List[Dict[str, Any]] = []
            self._record_step(
                run_id,
                steps,
                "verify_bill_proposer_integrity",
                manager.verify_bill_proposer_integrity(limit=limit),
            )
            return steps

        return self._run("bill.ingest_verify", params, execute)

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
                    self._record_step(
                        run_id,
                        steps,
                        f"skip_{upsert_name}",
                        {"status": "empty", "reason": "no artifact"},
                    )
            return steps

        return self._run("bill.status_sync", params, execute)

    def run_bill_search_rebuild(
        self,
        *,
        mode: str = "dry_run",
        limit: int = 500,
    ) -> Dict[str, Any]:
        params = {"mode": mode, "limit": limit}

        def execute(run_id: str) -> List[Dict[str, Any]]:
            manager = _build_workflow_manager(mode)
            steps: List[Dict[str, Any]] = []
            self._record_step(
                run_id,
                steps,
                "rebuild_bill_search_documents",
                manager.rebuild_bill_search_documents(limit=limit),
            )
            return steps

        return self._run("bill.search_rebuild", params, execute)

    def run_legal_term_dictionary_sync(
        self,
        *,
        mode: str = "dry_run",
        query: str = "가",
        page_size: int = 100,
        start_page: int = 1,
        max_pages: int = 1,
        max_retries: int = 0,
        limit: int | None = None,
    ) -> Dict[str, Any]:
        params = {
            "mode": mode,
            "query": query,
            "page_size": page_size,
            "start_page": start_page,
            "max_pages": max_pages,
            "max_retries": max_retries,
            "limit": limit,
        }

        def execute(run_id: str) -> List[Dict[str, Any]]:
            from lawdigest_ai.processor.legal_term_dictionary_sync import run_legal_term_dictionary_sync

            steps: List[Dict[str, Any]] = []
            self._record_step(
                run_id,
                steps,
                "sync_legal_term_dictionary",
                run_legal_term_dictionary_sync(
                    mode=mode,
                    query=query,
                    page_size=page_size,
                    start_page=start_page,
                    max_pages=max_pages,
                    max_retries=max_retries,
                    limit=limit,
                ),
            )
            return steps

        return self._run("legal_term.dictionary_sync", params, execute)

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
        cli_provider: str = "codex",
        limit: int = 20,
        batch_size: int = 5,
        output_path: str = "/tmp/lawdigest_ai_summary_results.json",
        stop_on_error: bool = False,
        read_mode: str | None = None,
        target_mode: str = "missing",
    ) -> Dict[str, Any]:
        total_limit = limit
        if total_limit < 1:
            raise ValueError("limit는 1 이상이어야 합니다.")
        if batch_size < 1:
            raise ValueError("batch_size는 1 이상이어야 합니다.")

        chunk_size = min(batch_size, MAX_AI_SUMMARY_CHUNK_SIZE)
        params = {
            "mode": mode,
            "cli_provider": cli_provider,
            "limit": total_limit,
            "total_limit": total_limit,
            "batch_size": batch_size,
            "chunk_size": chunk_size,
            "max_chunk_size": MAX_AI_SUMMARY_CHUNK_SIZE,
            "output_path": output_path,
            "stop_on_error": stop_on_error,
            "read_mode": read_mode,
            "target_mode": target_mode,
        }

        def execute(run_id: str) -> List[Dict[str, Any]]:
            from lawdigest_ai.processor.gemini_repair_pipeline import run_gemini_repair_pipeline

            steps: List[Dict[str, Any]] = []
            chunk_results: List[Dict[str, Any]] = []
            remaining = total_limit
            chunk_number = 1
            while remaining > 0:
                chunk_limit = min(remaining, chunk_size)
                chunk_output_path = (
                    output_path if total_limit <= chunk_size else _chunk_output_path(output_path, chunk_number)
                )
                chunk_result = run_gemini_repair_pipeline(
                    mode=mode,
                    limit=chunk_limit,
                    batch_size=chunk_limit,
                    output_path=chunk_output_path,
                    stop_on_error=stop_on_error,
                    read_mode=read_mode,
                    target_mode=target_mode,
                    cli_provider=cli_provider,
                )
                chunk_stats = chunk_result.get("stats", {})
                chunk_results.append({
                    "chunk": chunk_number,
                    "requested_limit": chunk_limit,
                    "output_path": chunk_output_path,
                    "stats": chunk_stats,
                })
                processed_count = int(chunk_stats.get("processed_count") or 0)
                target_count = int(chunk_stats.get("target_count") or 0)
                if target_count == 0 or processed_count == 0:
                    break
                remaining -= target_count
                if target_count < chunk_limit:
                    break
                chunk_number += 1

            aggregate_stats = {
                "target_count": sum(int(item["stats"].get("target_count") or 0) for item in chunk_results),
                "processed_count": sum(int(item["stats"].get("processed_count") or 0) for item in chunk_results),
                "success_count": sum(int(item["stats"].get("success_count") or 0) for item in chunk_results),
                "failure_count": sum(int(item["stats"].get("failure_count") or 0) for item in chunk_results),
                "db_upserted_count": sum(int(item["stats"].get("db_upserted_count") or 0) for item in chunk_results),
                "token_usage_available_count": sum(
                    int(item["stats"].get("token_usage_available_count") or 0) for item in chunk_results
                ),
                "usage_totals": _merge_usage_totals(chunk_results),
            }
            aggregate_result = {
                "execution_mode": mode,
                "requested_limit": total_limit,
                "total_limit": total_limit,
                "chunk_size": chunk_size,
                "max_chunk_size": MAX_AI_SUMMARY_CHUNK_SIZE,
                "batch_size_requested": batch_size,
                "stop_on_error": stop_on_error,
                "read_mode": read_mode,
                "target_mode": target_mode,
                "cli_provider": cli_provider,
                "stats": aggregate_stats,
                "chunks": chunk_results,
                "output_path": output_path,
            }
            if total_limit > chunk_size:
                _write_json_output(aggregate_result, output_path)
            self._record_step(run_id, steps, step, aggregate_result)
            return steps

        return self._run(command, params, execute)

    def run_ai_summary(
        self,
        *,
        mode: str = "dry_run",
        engine: str = "agent",
        cli_provider: str = "codex",
        limit: int = 20,
        batch_size: int = 5,
        output_path: str = "/tmp/lawdigest_ai_summary_results.json",
        output_dir: str = "/tmp/lawdigest-bill-agent-reports",
        stop_on_error: bool = False,
        read_mode: str | None = None,
        target_mode: str = "missing",
        codex_model: str | None = None,
        target: str = "passed",
        concurrency: int = 1,
        report_mode: str = "deep_report",
        batch_session_size: int = 5,
        weekly_usage_before: float | None = None,
        weekly_usage_after: float | None = None,
        five_hour_usage_before: float | None = None,
        five_hour_usage_after: float | None = None,
        inspection: bool = False,
    ) -> Dict[str, Any]:
        if engine == "agent":
            return self._run_agentic_bill_report(
                command="ai.summary",
                passed_step="generate_agentic_summary_reports",
                all_step="generate_all_agentic_summary_reports",
                mode=mode,
                limit=limit,
                output_dir=output_dir,
                read_mode=read_mode,
                codex_model=codex_model,
                stop_on_error=stop_on_error,
                target=target,
                concurrency=concurrency,
                report_mode=report_mode,
                batch_session_size=batch_session_size,
                weekly_usage_before=weekly_usage_before,
                weekly_usage_after=weekly_usage_after,
                five_hour_usage_before=five_hour_usage_before,
                five_hour_usage_after=five_hour_usage_after,
                inspection=inspection,
            )
        if engine != "cli":
            raise ValueError("engine은 agent 또는 cli여야 합니다.")
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
        cli_provider: str = "codex",
        limit: int = 20,
        batch_size: int = 5,
        output_path: str = "/tmp/lawdigest_ai_summary_results.json",
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

    def _run_agentic_bill_report(
        self,
        *,
        command: str,
        passed_step: str,
        all_step: str,
        mode: str = "dry_run",
        limit: int = 5,
        output_dir: str = "/tmp/lawdigest-bill-agent-reports",
        read_mode: str | None = None,
        codex_model: str | None = None,
        stop_on_error: bool = False,
        target: str = "passed",
        concurrency: int = 1,
        report_mode: str = "deep_report",
        batch_session_size: int = 5,
        weekly_usage_before: float | None = None,
        weekly_usage_after: float | None = None,
        five_hour_usage_before: float | None = None,
        five_hour_usage_after: float | None = None,
        inspection: bool = False,
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
            "report_mode": report_mode,
            "batch_session_size": batch_session_size,
            "usage_meter": usage_meter,
            "inspection": inspection,
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
                "report_mode": report_mode,
                "batch_session_size": batch_session_size,
                "inspection": inspection,
            }
            if usage_meter is not None:
                report_kwargs["usage_meter"] = usage_meter
            report = run_agentic_bill_reports(
                **report_kwargs,
            )
            step_name = passed_step
            if target == "all":
                step_name = all_step
            elif target == "pending":
                step_name = "generate_pending_agentic_summary_reports"
            self._record_step(
                run_id,
                steps,
                step_name,
                report,
            )
            stats = report.get("stats", {})
            if stats.get("target_count", 0) > 0 and stats.get("success_count", 0) == 0:
                raise RuntimeError("모든 법안 리포트 생성에 실패했습니다.")
            return steps

        return self._run(command, params, execute)

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
        report_mode: str = "deep_report",
        batch_session_size: int = 5,
        weekly_usage_before: float | None = None,
        weekly_usage_after: float | None = None,
        five_hour_usage_before: float | None = None,
        five_hour_usage_after: float | None = None,
        inspection: bool = False,
    ) -> Dict[str, Any]:
        return self._run_agentic_bill_report(
            command="bill.agent_report",
            passed_step="generate_passed_bill_reports",
            all_step="generate_all_bill_reports",
            mode=mode,
            limit=limit,
            output_dir=output_dir,
            read_mode=read_mode,
            codex_model=codex_model,
            stop_on_error=stop_on_error,
            target=target,
            concurrency=concurrency,
            report_mode=report_mode,
            batch_session_size=batch_session_size,
            weekly_usage_before=weekly_usage_before,
            weekly_usage_after=weekly_usage_after,
            five_hour_usage_before=five_hour_usage_before,
            five_hour_usage_after=five_hour_usage_after,
            inspection=inspection,
        )
