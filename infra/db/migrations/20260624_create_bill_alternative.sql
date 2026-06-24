CREATE TABLE IF NOT EXISTS BillAlternative (
  bill_alternative_id BIGINT NOT NULL AUTO_INCREMENT,
  alternative_bill_id VARCHAR(255) NOT NULL,
  original_bill_id VARCHAR(255) NOT NULL,
  created_date DATETIME(6) DEFAULT NULL,
  modified_date DATETIME(6) DEFAULT NULL,
  PRIMARY KEY (bill_alternative_id),
  UNIQUE KEY uq_bill_alternative_pair (alternative_bill_id, original_bill_id),
  KEY idx_bill_alternative_alternative_bill_id (alternative_bill_id),
  KEY idx_bill_alternative_original_bill_id (original_bill_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
