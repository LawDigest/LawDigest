-- Deprecated: summary tags are stored in BillSummaryTag instead of Bill.summary_tags.
-- Keeping this migration as a no-op prevents unsafe ALTER TABLE Bill on large FULLTEXT-backed tables.
SELECT 1;
