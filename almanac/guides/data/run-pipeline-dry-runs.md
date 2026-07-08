---
title: Run Pipeline Dry Runs
topics: [concepts]
sources:
  - id: pipeline-runbook
    type: file
    path: docs/data/법안 데이터 파이프라인/pipeline_restart_runbook.md
  - id: runtime-cli
    type: file
    path: services/data/src/lawdigest_data/runtime/cli.py
  - id: pipeline-runtime
    type: file
    path: services/data/src/lawdigest_data/runtime/pipeline.py
  - id: workflow-manager
    type: file
    path: services/data/src/lawdigest_data/core/WorkFlowManager.py
---

# Run Pipeline Dry Runs

Pipeline dry runs are the safe first execution mode for Lawdigest data operations. They let a maintainer exercise the `lawdigest-pipeline` command surface, source fetches, artifact creation, and append-only run logging without committing pipeline results to the production database. Use them before bill ingest, bill status sync, bill search-document rebuild, AI summary/report work, and provider batch operations whenever the command, source data, date range, or environment is not already verified [@pipeline-runbook].

This page is related to [Pipeline Runtime](../../architecture/data/pipeline-runtime.md), [Pipeline CLI](../../reference/data/pipeline-cli.md), and [Pipeline Run Log](../../reference/data/pipeline-run-log.md).

## When To Use

Use a dry run before changing a scheduled command, testing a new date range, validating external source access, checking a rebuild count, or preparing a production run. The CLI defaults most data commands to `--mode dry_run`, including `bill-ingest`, `bill-status-sync`, `bill-search-rebuild`, `ai-batch-submit`, `ai-batch-ingest`, `ai-repair-native`, `ai-summary`, and `bill-agent-report` [@runtime-cli].

Dry runs are especially useful for commands that can read production data but should not write to it. The runbook shows `ai-summary --mode dry_run --read-mode prod`, which reads production candidates and writes output files instead of applying DB updates [@pipeline-runbook].

## Before Running

Work from the repository root and set `PYTHONPATH` so the data and AI packages resolve:

```bash
cd /home/ubuntu/project/Lawdigest
PYTHONPATH=services/data/src:services/ai/src python -m lawdigest_data.runtime.cli --help
```

The runbook also allows the installed console script `lawdigest-pipeline --help` when the package environment is installed [@pipeline-runbook].

Decide where run logs should go. By default, the runtime writes append-only JSONL events to `/tmp/lawdigest-pipeline/pipeline-runs.jsonl`; `LAWDIGEST_PIPELINE_LOG_DIR` can move that log directory [@pipeline-runtime] [@pipeline-runbook].

## Ordered Steps

1. Inspect the command help.

   ```bash
   PYTHONPATH=services/data/src:services/ai/src python -m lawdigest_data.runtime.cli --help
   ```

   Confirm that the command exists and that the mode choices match the target operation. For example, `bill-search-rebuild` accepts `dry_run`, `test`, `prod`, and `test_db` modes and a `--limit` option [@runtime-cli].

2. Run the smallest useful dry run.

   For bill ingest:

   ```bash
   PYTHONPATH=services/data/src:services/ai/src python -m lawdigest_data.runtime.cli \
     bill-ingest \
     --mode dry_run \
     --start-date 2026-05-19 \
     --end-date 2026-05-19 \
     --age 22
   ```

   For status sync:

   ```bash
   PYTHONPATH=services/data/src:services/ai/src python -m lawdigest_data.runtime.cli \
     bill-status-sync \
     --mode dry_run \
     --start-date 2026-05-19 \
     --end-date 2026-05-19 \
     --age 22
   ```

   These command forms come from the data pipeline runbook [@pipeline-runbook].

3. For AI summary/report checks, keep concurrency and limit low.

   ```bash
   PYTHONPATH=services/data/src:services/ai/src python -m lawdigest_data.runtime.cli \
     ai-summary \
     --mode dry_run \
     --read-mode prod \
     --limit 1 \
     --target passed \
     --concurrency 1 \
     --output-dir /tmp/lawdigest-bill-agent-reports
   ```

   The runbook presents this as the standard AI summary dry-run shape [@pipeline-runbook].

4. Capture the printed JSON result.

   The CLI prints the runtime result as formatted JSON and returns exit code 0 only when `status` is `success` [@runtime-cli].

5. Inspect the run log.

   ```bash
   tail -n 20 /tmp/lawdigest-pipeline/pipeline-runs.jsonl
   ```

   Each run writes `run_started`, `step_finished`, and `run_finished` events with command, params, step result, status, and timestamps [@pipeline-runtime].

## Verification

Verify the top-level command status, the step names, and whether artifacts were produced. `PipelineRuntime.run_bill_ingest` records `fetch_bills`, `process_bills`, and `upsert_bills` steps, with skip steps when an earlier step produces no artifact [@pipeline-runtime]. `run_bill_status_sync` records lawmaker updates plus lifecycle and vote fetch/upsert steps [@pipeline-runtime].

For dry-run database safety, check the command-specific implementation. Bill persistence returns zero without writing when `WorkFlowManager` is in `dry_run` mode [@workflow-manager]. Search rebuild likewise returns the number of candidates and documents while reporting `upserted: 0` in dry-run mode [@workflow-manager].

For AI report dry runs, inspect the manifest or output JSON mentioned by the command output. The runbook uses `jq` against `/tmp/lawdigest-bill-agent-reports/manifest.json` for agent report review [@pipeline-runbook].

## Recovery Notes

If a dry run fails before producing artifacts, use the `traceback` field in the final `run_finished` event. `PipelineRuntime` records failed runs with the exception string and traceback before re-raising the error [@pipeline-runtime].

If a command produces a skip step, do not treat it as a successful data update. A skip means a prior fetch or process step did not produce the artifact needed by the next step [@pipeline-runtime].

If a dry run unexpectedly writes to the database, stop and inspect the mode normalization path before running any production command. The bill workflow normalizes `test` to `test_db`, `prod` to `prod`, and aliases such as `dryrun` to `dry_run`; unsupported values raise a `ValueError` [@workflow-manager].

If the log location is empty, check whether `--log-dir` or `LAWDIGEST_PIPELINE_LOG_DIR` sent events to a different directory. The CLI accepts a global `--log-dir` option before the subcommand [@runtime-cli].
