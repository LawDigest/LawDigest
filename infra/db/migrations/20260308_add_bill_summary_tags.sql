ALTER TABLE Bill
  ADD COLUMN IF NOT EXISTS summary_tags JSON NULL
  AFTER brief_summary;
