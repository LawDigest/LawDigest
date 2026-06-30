-- 검색을 BillSearchDocument로 이전(20260627)한 뒤, Bill의 FULLTEXT 인덱스를 정리한다.
-- Bill에 FULLTEXT가 있으면 ADD COLUMN이 ALGORITHM=COPY(전체 재구성)로 강제되므로,
-- 이를 제거해 이후 스키마 변경을 INPLACE/INSTANT로 만든다.
-- 인덱스 DROP은 InnoDB에서 온라인(ALGORITHM=INPLACE, LOCK=NONE)이라 무중단.
-- 멱등: 남아있는 FULLTEXT 인덱스가 있을 때만 한 번에 DROP.

SET @drop_fulltext_sql := (
  SELECT IF(
    COUNT(*) = 0,
    'SELECT 1',
    CONCAT(
      'ALTER TABLE Bill ',
      GROUP_CONCAT(CONCAT('DROP INDEX ', INDEX_NAME) SEPARATOR ', '),
      ', ALGORITHM=INPLACE, LOCK=NONE'
    )
  )
  FROM (
    SELECT DISTINCT INDEX_NAME
    FROM INFORMATION_SCHEMA.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'Bill'
      AND INDEX_TYPE = 'FULLTEXT'
  ) ft
);

PREPARE stmt FROM @drop_fulltext_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
