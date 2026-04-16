CREATE TABLE IF NOT EXISTS IngestCheckpoint (
  source_name VARCHAR(100) NOT NULL,
  assembly_number INT NOT NULL,
  last_reference_date DATE NULL,
  metadata_json JSON NULL,
  created_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  modified_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (source_name, assembly_number)
);
