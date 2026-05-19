CREATE TABLE IF NOT EXISTS BillSummaryTag (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  bill_id VARCHAR(255) NOT NULL,
  tag VARCHAR(100) NOT NULL,
  created_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  modified_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_bill_summary_tag_bill_tag (bill_id, tag),
  INDEX idx_bill_summary_tag_bill_id (bill_id),
  INDEX idx_bill_summary_tag_tag (tag)
);
