SET @legacy_batch_id_unique := (
  SELECT INDEX_NAME
  FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'ai_batch_jobs'
    AND NON_UNIQUE = 0
    AND COLUMN_NAME = 'batch_id'
  ORDER BY SEQ_IN_INDEX
  LIMIT 1
);

SET @drop_legacy_unique_sql := IF(
  @legacy_batch_id_unique IS NULL,
  'SELECT 1',
  CONCAT('ALTER TABLE ai_batch_jobs DROP INDEX `', @legacy_batch_id_unique, '`')
);

PREPARE stmt FROM @drop_legacy_unique_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

ALTER TABLE ai_batch_jobs
  ADD COLUMN IF NOT EXISTS provider VARCHAR(32) NOT NULL DEFAULT 'openai' AFTER id,
  ADD UNIQUE KEY uq_ai_batch_jobs_provider_batch_id (provider, batch_id),
  ADD INDEX idx_ai_batch_jobs_provider_status_created_at (provider, status, created_at);
