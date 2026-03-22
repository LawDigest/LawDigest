CREATE TABLE IF NOT EXISTS ai_batch_jobs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  batch_id VARCHAR(128) NOT NULL UNIQUE,
  status VARCHAR(32) NOT NULL,
  input_file_id VARCHAR(128) NULL,
  output_file_id VARCHAR(128) NULL,
  error_file_id VARCHAR(128) NULL,
  endpoint VARCHAR(64) NOT NULL DEFAULT '/v1/chat/completions',
  model_name VARCHAR(64) NOT NULL,
  total_count INT NOT NULL DEFAULT 0,
  success_count INT NOT NULL DEFAULT 0,
  failed_count INT NOT NULL DEFAULT 0,
  submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at DATETIME NULL,
  error_message TEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_ai_batch_jobs_status (status),
  INDEX idx_ai_batch_jobs_created_at (created_at)
);

CREATE TABLE IF NOT EXISTS ai_batch_items (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  job_id BIGINT NOT NULL,
  bill_id VARCHAR(100) NOT NULL,
  custom_id VARCHAR(150) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'SUBMITTED',
  retry_count INT NOT NULL DEFAULT 0,
  error_message TEXT NULL,
  processed_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_ai_batch_items_job_bill (job_id, bill_id),
  INDEX idx_ai_batch_items_bill (bill_id),
  INDEX idx_ai_batch_items_status (status),
  CONSTRAINT fk_ai_batch_items_job
    FOREIGN KEY (job_id) REFERENCES ai_batch_jobs(id)
    ON DELETE CASCADE
);
