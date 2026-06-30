-- Bill.category: AI/위원회 분류로 채우는 생활영역 분야 코드(예: economy, health, unknown).
-- 설계: output/tab-prototypes/FIELD_TAXONOMY.md (v4). 멱등(information_schema 가드).
-- 백필(위원회 매핑·본회의 AI)은 별도 스크립트에서 수행한다.

SET @bill_category_column_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'Bill'
    AND COLUMN_NAME = 'category'
);

SET @add_bill_category_column_sql := IF(
  @bill_category_column_exists = 0,
  'ALTER TABLE Bill ADD COLUMN category VARCHAR(32) NULL',
  'SELECT 1'
);

PREPARE stmt FROM @add_bill_category_column_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @bill_category_index_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'Bill'
    AND INDEX_NAME = 'idx_bill_category'
);

SET @add_bill_category_index_sql := IF(
  @bill_category_index_exists = 0,
  'ALTER TABLE Bill ADD INDEX idx_bill_category (category)',
  'SELECT 1'
);

PREPARE stmt FROM @add_bill_category_index_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
