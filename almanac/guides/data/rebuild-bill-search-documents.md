---
title: Rebuild Bill Search Documents
topics: [concepts]
sources:
  - id: runtime-cli
    type: file
    path: services/data/src/lawdigest_data/runtime/cli.py
  - id: pipeline-runtime
    type: file
    path: services/data/src/lawdigest_data/runtime/pipeline.py
  - id: search-document-builder
    type: file
    path: services/data/src/lawdigest_data/bills/search_document.py
  - id: database-manager
    type: file
    path: services/data/src/lawdigest_data/connectors/DatabaseManager.py
  - id: workflow-manager
    type: file
    path: services/data/src/lawdigest_data/core/WorkFlowManager.py
  - id: split-review
    type: file
    path: docs/data/bill-summary-search-split-review.md
---

# Rebuild Bill Search Documents

Rebuilding bill search documents refreshes the derived `BillSearchDocument` rows used by keyword search. Use this task when READY bills are missing from search, when bill summary fields have changed, after deploying the search-document schema, or before verifying that backend search no longer depends on FULLTEXT indexes on the hot `Bill` table. The rebuild is designed to update only eligible missing or stale documents, not every bill on every run [@database-manager].

This page is related to [Bill Search Document](../../architecture/data/bill-search-document.md), [Bill Data Quality States](../../concepts/data/bill-data-quality-states.md), and [Pipeline CLI](../../reference/data/pipeline-cli.md).

## When To Use

Run this guide after `BillSearchDocument` exists, after a bill ingest or AI summary operation has changed searchable text, or when a search smoke test suggests a READY bill cannot be found by a keyword that should be present. The split review identifies the rebuild command as the asynchronous path for maintaining the separate search table [@split-review].

Do not use this task to repair canonical bill data. If a bill is `PENDING` or `PARTIAL`, or if `Bill.summary` is empty, the candidate query intentionally excludes it from search-document rebuild [@database-manager].

## Ordered Steps

1. Confirm the command surface.

   ```bash
   cd /home/ubuntu/project/Lawdigest
   PYTHONPATH=services/data/src:services/ai/src python -m lawdigest_data.runtime.cli \
     bill-search-rebuild --help
   ```

   The command accepts `--mode` with `dry_run`, `test`, `prod`, or `test_db`, and `--limit` with a default of 500 [@runtime-cli].

2. Run a small dry run.

   ```bash
   PYTHONPATH=services/data/src:services/ai/src python -m lawdigest_data.runtime.cli \
     bill-search-rebuild \
     --mode dry_run \
     --limit 25
   ```

   The runtime dispatches this command to `PipelineRuntime.run_bill_search_rebuild`, which records one step named `rebuild_bill_search_documents` [@pipeline-runtime].

3. Inspect the JSON result.

   In dry-run mode, `WorkFlowManager.rebuild_bill_search_documents` fetches candidates, builds documents, and returns `upserted: 0` without writing to the database [@workflow-manager]. A useful dry run should show how many candidates were selected and how many documents would be built.

4. If the dry run is expected, run the target mode.

   ```bash
   PYTHONPATH=services/data/src:services/ai/src python -m lawdigest_data.runtime.cli \
     bill-search-rebuild \
     --mode prod \
     --limit 500
   ```

   In non-dry-run modes, the workflow writes built documents with `DatabaseManager.upsert_bill_search_documents` [@workflow-manager] [@database-manager].

5. Repeat until the candidate count reaches zero or the remaining count is understood.

   Candidate selection is limited by `--limit` and ordered by source modification timestamp and bill id, so large backfills may require multiple runs [@database-manager].

## What Gets Rebuilt

The candidate query selects from `Bill`, left joins `BillSearchDocument`, and requires all of these conditions: `b.ingest_status = 'READY'`, `b.summary IS NOT NULL`, `b.summary <> ''`, and either no document row or a source modification timestamp newer than the stored document timestamp [@database-manager].

The builder normalizes whitespace and composes `search_text` from bill name, bill name, bill name, brief summary, brief summary, AI summary, and raw summary. It returns `None` when no `bill_id` is available [@search-document-builder].

The upsert writes copied field text, combined `search_text`, `source_modified_date`, and a fresh `rebuilt_date`. Duplicate bill ids update the existing document row [@database-manager].

## Verification

Check the runtime result first. A successful run should have `status: success`, `command: bill.search_rebuild`, and a `rebuild_bill_search_documents` step [@pipeline-runtime].

Then verify candidate exhaustion with another dry run:

```bash
PYTHONPATH=services/data/src:services/ai/src python -m lawdigest_data.runtime.cli \
  bill-search-rebuild \
  --mode dry_run \
  --limit 25
```

If the second dry run still reports candidates, compare the count with the previous limit. A nonzero count may simply mean the previous run processed one page of a larger backlog.

For search behavior, use an application-level keyword known to occur in a READY bill. Backend search reads `BillSearchDocument.search_text` and joins back to READY bills, so a good verification checks both the document row and the user-facing search route [@database-manager].

## Recovery Notes

If the command fails before writing, inspect the append-only pipeline log. The runtime records failed commands with the exception message and traceback [@pipeline-runtime].

If documents are built but not upserted in production mode, verify the mode value and database connection path. `dry_run` intentionally returns zero upserts; `test` is normalized to `test_db`, while `prod` uses the production DB configuration through the workflow manager [@workflow-manager].

If search still misses a bill after rebuild, check whether the bill is actually eligible. Incomplete bills, bills without raw summaries, and non-READY bills are outside the search-document rebuild contract [@database-manager].

If a document contains outdated text, compare `Bill.modified_date` or `Bill.created_date` with `BillSearchDocument.source_modified_date`. The candidate query uses that comparison to decide staleness, so missing or unexpected source timestamps can explain why a row was not selected [@database-manager].
