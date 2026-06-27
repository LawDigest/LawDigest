# pt-online-schema-change runbook

Date: 2026-06-27

## Purpose

Use `pt-online-schema-change` for production MySQL schema changes that would otherwise rebuild a hot table and hold metadata locks for too long.

The immediate target is:

```sql
ALTER TABLE Bill
    MODIFY COLUMN summary TEXT NOT NULL;
```

## Installed tool

The production host has Percona Toolkit installed:

```bash
pt-online-schema-change --version
# pt-online-schema-change 3.2.1
```

Reference:
- https://docs.percona.com/percona-toolkit/pt-online-schema-change.html

## Preconditions

Run these checks before any production execution:

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

Expected state before applying `summary TEXT NOT NULL`:

- `null_summary_count = 0`
- `empty_summary_count = 0`
- `SHOW TRIGGERS LIKE 'Bill'` returns 0 rows
- Take and verify a DB backup before execution
- Confirm no long-running `Bill` queries are active
- Run during a low-traffic window

## Foreign key note

`Bill` is referenced by child tables, including `BillLike`, `BillProposer`, `BillTimeline`, `RepresentativeProposer`, `VoteParty`, and `VoteRecord`.

Use `--alter-foreign-keys-method=auto` first. Do not use `drop_swap` without a separate rollback plan.

## Dry run

Use environment variables or a MySQL defaults file. Do not paste credentials into shell history.

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

## Execute

Run only after the dry run succeeds and the preconditions have been checked.

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

## Verification

```sql
SHOW COLUMNS FROM Bill LIKE 'summary';

SELECT COUNT(*) AS null_summary_count
FROM Bill
WHERE summary IS NULL;

SHOW FULL PROCESSLIST;
```

Expected result:

- `SHOW COLUMNS` reports `Null = NO` for `summary`
- `null_summary_count = 0`
- no lingering metadata-lock waiters

## Rollback posture

`pt-online-schema-change` swaps the altered table into place at the end. If execution fails before the swap, inspect and clean up only the tool-created shadow table/triggers after confirming the original `Bill` table is intact.

Do not manually drop any table or trigger in production without first checking the generated object names and current table state.
