-- Bill.summary is required for user-visible bill ingestion.
-- Preflight:
--   SELECT COUNT(*) FROM Bill WHERE summary IS NULL;
-- Apply only after the count is 0. On MySQL this ALTER may copy the Bill table,
-- so run it in a maintenance window or with an online schema change tool.

ALTER TABLE Bill
    MODIFY COLUMN summary TEXT NOT NULL;
