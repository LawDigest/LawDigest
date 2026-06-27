from __future__ import annotations

import argparse
import json
from typing import Sequence

from lawdigest_data.runtime.pipeline import DEFAULT_LOG_DIR, PipelineRuntime


def _print_result(result: dict) -> None:
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


def _add_cli_summary_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--mode", default="dry_run", choices=["dry_run", "test", "prod"])
    parser.add_argument("--cli-provider", default="gemini", choices=["gemini", "codex", "claude"])
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--output-path", default="/tmp/gemini_ai_summary_results.json")
    parser.add_argument("--stop-on-error", action="store_true")
    parser.add_argument("--read-mode", choices=["test", "prod"])
    parser.add_argument("--target-mode", default="missing", choices=["missing", "latest"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lawdigest 자체 데이터 파이프라인 런타임")
    parser.add_argument("--log-dir", default=str(DEFAULT_LOG_DIR), help="pipeline-runs.jsonl 저장 디렉터리")

    subparsers = parser.add_subparsers(dest="command", required=True)

    bill_ingest = subparsers.add_parser("bill-ingest", help="법안 수집 -> 처리 -> DB 반영")
    bill_ingest.add_argument("--mode", default="dry_run", choices=["dry_run", "test", "prod"])
    bill_ingest.add_argument("--start-date")
    bill_ingest.add_argument("--end-date")
    bill_ingest.add_argument("--age", default="22")

    status_sync = subparsers.add_parser("bill-status-sync", help="의원/법안 lifecycle/vote 상태 동기화")
    status_sync.add_argument("--mode", default="dry_run", choices=["dry_run", "test", "prod", "test_db"])
    status_sync.add_argument("--start-date")
    status_sync.add_argument("--end-date")
    status_sync.add_argument("--age", default="22")

    search_rebuild = subparsers.add_parser("bill-search-rebuild", help="법안 검색 문서 비동기 재빌드")
    search_rebuild.add_argument("--mode", default="dry_run", choices=["dry_run", "test", "prod", "test_db"])
    search_rebuild.add_argument("--limit", type=int, default=500)

    batch_submit = subparsers.add_parser("ai-batch-submit", help="provider batch 요약 요청 제출")
    batch_submit.add_argument("--mode", default="dry_run", choices=["dry_run", "test", "prod"])
    batch_submit.add_argument("--provider", default="openai", choices=["openai", "gemini"])
    batch_submit.add_argument("--limit", type=int, default=200)
    batch_submit.add_argument("--model")

    batch_ingest = subparsers.add_parser("ai-batch-ingest", help="provider batch 요약 결과 회수")
    batch_ingest.add_argument("--mode", default="dry_run", choices=["dry_run", "test", "prod"])
    batch_ingest.add_argument("--provider", default="all", choices=["all", "openai", "gemini"])
    batch_ingest.add_argument("--max-jobs", type=int, default=10)

    native_repair = subparsers.add_parser("ai-repair-native", help="OpenAI/Gemini API 기반 결측 요약 복구")
    native_repair.add_argument("--mode", default="dry_run", choices=["dry_run", "test", "prod"])
    native_repair.add_argument("--provider", default="openai", choices=["openai", "gemini"])
    native_repair.add_argument("--limit", type=int, default=200)
    native_repair.add_argument("--batch-size", type=int, default=10)
    native_repair.add_argument("--model")
    native_repair.add_argument("--output-path", default="/tmp/lawdigest_missing_summaries.json")

    realtime_summary = subparsers.add_parser("ai-summary", help="Gemini CLI 기반 실시간 결측 요약")
    _add_cli_summary_args(realtime_summary)

    cli_repair = subparsers.add_parser("ai-repair-cli", help="Gemini/Codex/Claude CLI 기반 결측 요약 복구")
    _add_cli_summary_args(cli_repair)

    agent_report = subparsers.add_parser("bill-agent-report", help="Codex MCP 에이전트 기반 법안 종합 리포트")
    agent_report.add_argument("--mode", default="dry_run", choices=["dry_run", "test", "prod"])
    agent_report.add_argument("--limit", type=int, default=5)
    agent_report.add_argument("--output-dir", default="/tmp/lawdigest-bill-agent-reports")
    agent_report.add_argument("--read-mode", choices=["test", "prod"])
    agent_report.add_argument("--codex-model")
    agent_report.add_argument("--target", default="passed", choices=["passed", "all"])
    agent_report.add_argument("--concurrency", type=int, default=1)
    agent_report.add_argument("--weekly-usage-before", type=float)
    agent_report.add_argument("--weekly-usage-after", type=float)
    agent_report.add_argument("--five-hour-usage-before", type=float)
    agent_report.add_argument("--five-hour-usage-after", type=float)
    agent_report.add_argument("--inspection", action="store_true", help="에이전트 실행 감사용 검사 로그를 함께 저장")
    agent_report.add_argument("--stop-on-error", action="store_true")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    runtime = PipelineRuntime(log_dir=args.log_dir)

    if args.command == "bill-ingest":
        result = runtime.run_bill_ingest(
            mode=args.mode,
            start_date=args.start_date,
            end_date=args.end_date,
            age=args.age,
        )
    elif args.command == "bill-status-sync":
        result = runtime.run_bill_status_sync(
            mode=args.mode,
            start_date=args.start_date,
            end_date=args.end_date,
            age=args.age,
        )
    elif args.command == "bill-search-rebuild":
        result = runtime.run_bill_search_rebuild(
            mode=args.mode,
            limit=args.limit,
        )
    elif args.command == "ai-batch-submit":
        result = runtime.run_ai_batch_submit(
            mode=args.mode,
            provider=args.provider,
            limit=args.limit,
            model=args.model,
        )
    elif args.command == "ai-batch-ingest":
        result = runtime.run_ai_batch_ingest(
            mode=args.mode,
            provider=args.provider,
            max_jobs=args.max_jobs,
        )
    elif args.command == "ai-repair-native":
        result = runtime.run_ai_native_repair(
            mode=args.mode,
            provider=args.provider,
            limit=args.limit,
            batch_size=args.batch_size,
            model=args.model,
            output_path=args.output_path,
        )
    elif args.command == "ai-summary":
        result = runtime.run_ai_summary(
            mode=args.mode,
            cli_provider=args.cli_provider,
            limit=args.limit,
            batch_size=args.batch_size,
            output_path=args.output_path,
            stop_on_error=args.stop_on_error,
            read_mode=args.read_mode,
            target_mode=args.target_mode,
        )
    elif args.command == "ai-repair-cli":
        result = runtime.run_ai_cli_repair(
            mode=args.mode,
            cli_provider=args.cli_provider,
            limit=args.limit,
            batch_size=args.batch_size,
            output_path=args.output_path,
            stop_on_error=args.stop_on_error,
            read_mode=args.read_mode,
            target_mode=args.target_mode,
        )
    elif args.command == "bill-agent-report":
        result = runtime.run_bill_agent_report(
            mode=args.mode,
            limit=args.limit,
            output_dir=args.output_dir,
            read_mode=args.read_mode,
            codex_model=args.codex_model,
            stop_on_error=args.stop_on_error,
            target=args.target,
            concurrency=args.concurrency,
            weekly_usage_before=args.weekly_usage_before,
            weekly_usage_after=args.weekly_usage_after,
            five_hour_usage_before=args.five_hour_usage_before,
            five_hour_usage_after=args.five_hour_usage_after,
            inspection=args.inspection,
        )
    else:
        parser.error(f"unsupported command: {args.command}")

    _print_result(result)
    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
