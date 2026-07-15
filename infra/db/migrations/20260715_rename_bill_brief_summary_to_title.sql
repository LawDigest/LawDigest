-- Rename the generated bill card title fields without copying table data.
--
-- Preconditions:
--   * MySQL 8.0.28+ (production baseline: 8.0.35)
--   * all AI/data jobs that write Bill are paused
--   * the backend and web are in a coordinated maintenance window
--   * no views, generated columns, triggers, or stored routines reference the old names
--
-- The dynamic guards make a retry safe after either rename has completed. An
-- ambiguous schema (both columns present or both absent) intentionally fails.

SET @previous_lock_wait_timeout := @@SESSION.lock_wait_timeout;
SET SESSION lock_wait_timeout = 10;

SELECT COUNT(*)
INTO @bill_old_title_column_count
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'Bill'
  AND COLUMN_NAME = 'brief_summary';

SELECT COUNT(*)
INTO @bill_new_title_column_count
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'Bill'
  AND COLUMN_NAME = 'title';

SET @rename_bill_title_sql := CASE
    WHEN @bill_old_title_column_count = 1 AND @bill_new_title_column_count = 0
        THEN 'ALTER TABLE `Bill` RENAME COLUMN `brief_summary` TO `title`, ALGORITHM=INSTANT'
    WHEN @bill_old_title_column_count = 0 AND @bill_new_title_column_count = 1
        THEN 'SELECT ''Bill.title already migrated'' AS migration_status'
    ELSE 'SELECT invalid_bill_title_migration_state FROM `Bill` LIMIT 1'
END;

PREPARE rename_bill_title_statement FROM @rename_bill_title_sql;
EXECUTE rename_bill_title_statement;
DEALLOCATE PREPARE rename_bill_title_statement;

SELECT COUNT(*)
INTO @search_old_title_column_count
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'BillSearchDocument'
  AND COLUMN_NAME = 'brief_summary_text';

SELECT COUNT(*)
INTO @search_new_title_column_count
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'BillSearchDocument'
  AND COLUMN_NAME = 'title_text';

SET @rename_search_title_sql := CASE
    WHEN @search_old_title_column_count = 1 AND @search_new_title_column_count = 0
        THEN 'ALTER TABLE `BillSearchDocument` RENAME COLUMN `brief_summary_text` TO `title_text`, ALGORITHM=INSTANT'
    WHEN @search_old_title_column_count = 0 AND @search_new_title_column_count = 1
        THEN 'SELECT ''BillSearchDocument.title_text already migrated'' AS migration_status'
    ELSE 'SELECT invalid_search_title_migration_state FROM `BillSearchDocument` LIMIT 1'
END;

PREPARE rename_search_title_statement FROM @rename_search_title_sql;
EXECUTE rename_search_title_statement;
DEALLOCATE PREPARE rename_search_title_statement;

SET SESSION lock_wait_timeout = @previous_lock_wait_timeout;

SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND (
      (TABLE_NAME = 'Bill' AND COLUMN_NAME IN ('brief_summary', 'title'))
      OR
      (TABLE_NAME = 'BillSearchDocument' AND COLUMN_NAME IN ('brief_summary_text', 'title_text'))
  )
ORDER BY TABLE_NAME, COLUMN_NAME;
