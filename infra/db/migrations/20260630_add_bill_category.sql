-- Bill.category: AI/위원회 분류로 채우는 생활영역 분야 코드(예: economy, health, unknown).
-- 설계: output/tab-prototypes/FIELD_TAXONOMY.md (v4). 멱등(information_schema 가드).
-- 백필(위원회 매핑·본회의 AI)은 별도 스크립트에서 수행한다.
--
-- 주의: Bill 테이블에 FULLTEXT 인덱스가 있어 ADD COLUMN이 ALGORITHM=INSTANT/INPLACE 불가
-- → ALGORITHM=COPY(전체 테이블 재구성)로만 수행된다(대용량 테이블은 수 분 소요).
-- 컬럼과 인덱스를 단일 ALTER로 묶어 테이블 복사를 1회만 하도록 한다.

SET @col_exists := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'Bill' AND COLUMN_NAME = 'category'
);
SET @idx_exists := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'Bill' AND INDEX_NAME = 'idx_bill_category'
);

SET @sql := CASE
  WHEN @col_exists = 0 AND @idx_exists = 0 THEN
    'ALTER TABLE Bill ADD COLUMN category VARCHAR(32) NULL, ADD INDEX idx_bill_category (category), ALGORITHM=COPY'
  WHEN @col_exists = 0 THEN
    'ALTER TABLE Bill ADD COLUMN category VARCHAR(32) NULL, ALGORITHM=COPY'
  WHEN @idx_exists = 0 THEN
    'ALTER TABLE Bill ADD INDEX idx_bill_category (category)'
  ELSE 'SELECT 1'
END;

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
