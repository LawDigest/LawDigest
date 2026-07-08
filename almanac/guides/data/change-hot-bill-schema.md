---
title: Change Hot Bill Schema
topics: [concepts]
sources:
  - id: pt-runbook
    type: file
    path: docs/data/pt-online-schema-change-runbook.md
  - id: summary-not-null-migration
    type: file
    path: infra/db/migrations/20260627_make_bill_summary_not_null.sql
  - id: drop-fulltext-migration
    type: file
    path: infra/db/migrations/20260701_drop_bill_fulltext_indexes.sql
  - id: ingest-status-migration
    type: file
    path: infra/db/migrations/20260416_add_bill_ingest_status.sql
  - id: bill-entity
    type: file
    path: services/backend/src/main/java/com/everyones/lawmaking/domain/entity/Bill.java
  - id: split-review
    type: file
    path: docs/data/bill-summary-search-split-review.md
---

# Change Hot Bill Schema

Changing the hot `Bill` schema is a high-risk data operation because the table is central to bill feeds, search, detail pages, ingest, and timeline-related writes. Lawdigest keeps a specific runbook for changes that would rebuild the production MySQL table or hold metadata locks for too long. The immediate documented case is changing `Bill.summary` to `TEXT NOT NULL`, but the same posture applies to other structural changes on the hot bill table [@pt-runbook].

This page is related to [Bill Schema And Migrations](../../reference/data/bill-schema-and-migrations.md), [Bill Data Quality States](../../concepts/data/bill-data-quality-states.md), and [Integration Test Policy](../verification/integration-test-policy.md).

## When To Use

Use this guide before applying production DDL to `Bill` when the change may copy or rebuild the table, interact with FULLTEXT indexes, change required source-data fields, or affect fields used to determine `READY`, `PARTIAL`, and `PENDING` states. The repository migration for `summary TEXT NOT NULL` warns that MySQL may copy the table and should be run in a maintenance window or through an online schema change tool [@summary-not-null-migration].

Do not use direct destructive operations on production data. The runbook explicitly warns against manually dropping tool-created tables or triggers without first checking generated names and original table state [@pt-runbook].

## Background

`Bill` contains identity, assembly number, name, proposer information, dates, stage, result, proposer kind, ingest status, raw summary, AI summary, brief summary, URL fields, category-related fields, and view count [@bill-entity]. The entity resolves ingest status from the presence of bill name, propose date, stage, raw summary, brief summary, and AI summary [@bill-entity].

Earlier production state coupled `Bill.summary` to both canonical source text and FULLTEXT search. A direct `ALTER TABLE Bill MODIFY COLUMN summary TEXT NOT NULL` used MySQL's table-copy path and held metadata locks long enough to block concurrent `Bill` updates [@split-review]. The search split and later FULLTEXT cleanup are meant to reduce this kind of schema-change pressure on the main table [@split-review] [@drop-fulltext-migration].

## Ordered Steps

1. Identify the exact DDL.

   For the documented summary case, the DDL is:

   ```sql
   ALTER TABLE Bill
       MODIFY COLUMN summary TEXT NOT NULL;
   ```

   This is the same operation recorded in the migration and the online schema change runbook [@summary-not-null-migration] [@pt-runbook].

2. Run preflight data checks.

   ```sql
   SELECT COUNT(*) AS null_summary_count
   FROM Bill
   WHERE summary IS NULL;

   SELECT COUNT(*) AS empty_summary_count
   FROM Bill
   WHERE summary = '';

   SHOW TRIGGERS LIKE 'Bill';

   SHOW CREATE TABLE Bill;
   ```

   The expected state for the summary change is zero null summaries, zero empty summaries, no existing `Bill` triggers, a verified DB backup, no long-running `Bill` queries, and a low-traffic execution window [@pt-runbook].

3. Check foreign key posture.

   `Bill` is referenced by child tables including `BillLike`, `BillProposer`, `BillTimeline`, `RepresentativeProposer`, `VoteParty`, and `VoteRecord`. The runbook says to start with `--alter-foreign-keys-method=auto` and not to use `drop_swap` without a separate rollback plan [@pt-runbook].

4. Run the online schema dry run.

   ```bash
   pt-online-schema-change \
     --dry-run \
     --alter "MODIFY COLUMN summary TEXT NOT NULL" \
     --alter-foreign-keys-method=auto \
     --check-alter \
     --check-unique-key-change \
     --max-load Threads_running=50 \
     --critical-load Threads_running=100 \
     --chunk-time=0.5 \
     --set-vars lock_wait_timeout=5 \
     h="$DB_HOST",P="${DB_PORT:-3306}",u="$DB_USER",p="$DB_PASSWORD",D="$DB_NAME",t=Bill
   ```

   The runbook uses environment variables or a MySQL defaults file and warns not to paste credentials into shell history [@pt-runbook].

5. Execute only after the dry run and preconditions pass.

   ```bash
   pt-online-schema-change \
     --execute \
     --alter "MODIFY COLUMN summary TEXT NOT NULL" \
     --alter-foreign-keys-method=auto \
     --check-alter \
     --check-unique-key-change \
     --max-load Threads_running=50 \
     --critical-load Threads_running=100 \
     --chunk-time=0.5 \
     --set-vars lock_wait_timeout=5 \
     h="$DB_HOST",P="${DB_PORT:-3306}",u="$DB_USER",p="$DB_PASSWORD",D="$DB_NAME",t=Bill
   ```

   This command should be run only after the dry run succeeds and the preflight checks are confirmed [@pt-runbook].

## Verification

Verify the schema and runtime state immediately after execution:

```sql
SHOW COLUMNS FROM Bill LIKE 'summary';

SELECT COUNT(*) AS null_summary_count
FROM Bill
WHERE summary IS NULL;

SHOW FULL PROCESSLIST;
```

For the summary change, `SHOW COLUMNS` should report `Null = NO`, the null count should remain zero, and there should be no lingering metadata-lock waiters [@pt-runbook].

For ingest-status-related schema changes, compare the migration rule with the entity rule. The migration sets READY when bill name, propose date, stage, and summary are present [@ingest-status-migration]. The current backend entity requires bill name, propose date, stage, raw summary, brief summary, and AI summary for READY [@bill-entity]. That difference matters when validating old rows against current application behavior.

For FULLTEXT cleanup, verify that the query has moved to `BillSearchDocument` before dropping indexes from `Bill`. The cleanup migration is explicitly described as a step after search moved to `BillSearchDocument` and uses an idempotent dynamic `ALTER TABLE Bill DROP INDEX ... ALGORITHM=INPLACE, LOCK=NONE` for remaining FULLTEXT indexes [@drop-fulltext-migration].

## Recovery Notes

If `pt-online-schema-change` fails before the final swap, inspect the original `Bill` table first. The runbook says to clean up only tool-created shadow tables or triggers after confirming the original table is intact [@pt-runbook].

If metadata-lock waiters appear, stop treating the change as a normal migration and inspect active `Bill` queries with `SHOW FULL PROCESSLIST`. The risk being managed is long metadata locks on a write-heavy table [@pt-runbook] [@split-review].

If preflight counts are not zero, do not force the NOT NULL change. Repair the underlying source data first, then rerun preflight.

If a future `Bill` DDL still uses table-copy behavior, check whether FULLTEXT indexes or other table features are forcing the algorithm. The FULLTEXT cleanup migration notes that FULLTEXT indexes on `Bill` can force ADD COLUMN operations into full table reconstruction [@drop-fulltext-migration].
