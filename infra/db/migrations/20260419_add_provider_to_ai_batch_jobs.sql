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

SET @provider_column_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'ai_batch_jobs'
    AND COLUMN_NAME = 'provider'
);

SET @add_provider_column_sql := IF(
  @provider_column_exists = 0,
  'ALTER TABLE ai_batch_jobs ADD COLUMN provider VARCHAR(32) NOT NULL DEFAULT ''openai'' AFTER id',
  'SELECT 1'
);

PREPARE stmt FROM @add_provider_column_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @provider_batch_unique_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'ai_batch_jobs'
    AND INDEX_NAME = 'uq_ai_batch_jobs_provider_batch_id'
);

SET @add_provider_batch_unique_sql := IF(
  @provider_batch_unique_exists = 0,
  'ALTER TABLE ai_batch_jobs ADD UNIQUE KEY uq_ai_batch_jobs_provider_batch_id (provider, batch_id)',
  'SELECT 1'
);

PREPARE stmt FROM @add_provider_batch_unique_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @provider_status_created_index_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'ai_batch_jobs'
    AND INDEX_NAME = 'idx_ai_batch_jobs_provider_status_created_at'
);

SET @add_provider_status_created_index_sql := IF(
  @provider_status_created_index_exists = 0,
  'ALTER TABLE ai_batch_jobs ADD INDEX idx_ai_batch_jobs_provider_status_created_at (provider, status, created_at)',
  'SELECT 1'
);

PREPARE stmt FROM @add_provider_status_created_index_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
