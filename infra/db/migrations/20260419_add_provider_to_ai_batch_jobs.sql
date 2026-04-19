ALTER TABLE ai_batch_jobs
  ADD COLUMN provider VARCHAR(32) NOT NULL DEFAULT 'openai' AFTER id,
  DROP INDEX batch_id,
  ADD UNIQUE KEY uq_ai_batch_jobs_provider_batch_id (provider, batch_id),
  ADD INDEX idx_ai_batch_jobs_provider_status_created_at (provider, status, created_at);
