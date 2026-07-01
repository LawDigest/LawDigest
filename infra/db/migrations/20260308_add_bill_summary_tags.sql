-- Bill.summary_tags (JSON) 추가 — AI 요약 태그 저장용(탐색 '지금 뜨는 키워드' 집계 소스).
-- MySQL 8은 ADD COLUMN IF NOT EXISTS 문법을 지원하지 않으므로 information_schema로 멱등 처리한다.
-- Bill의 FULLTEXT 인덱스 제거(20260701) 이후에는 INPLACE 온라인으로 적용된다.
SET @add_summary_tags := (
  SELECT IF(
    COUNT(*) > 0,
    'SELECT 1',
    'ALTER TABLE Bill ADD COLUMN summary_tags JSON NULL AFTER brief_summary'
  )
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'Bill'
    AND COLUMN_NAME = 'summary_tags'
);

PREPARE stmt FROM @add_summary_tags;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
