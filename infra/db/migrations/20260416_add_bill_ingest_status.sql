ALTER TABLE Bill
    MODIFY proposer_kind ENUM('CHAIRMAN', 'CONGRESSMAN', 'GOVERNMENT') DEFAULT 'CONGRESSMAN';

ALTER TABLE Bill
    ADD COLUMN ingest_status VARCHAR(20) NOT NULL DEFAULT 'PENDING' AFTER proposer_kind;

UPDATE Bill
SET ingest_status = CASE
    WHEN bill_name IS NOT NULL AND bill_name <> ''
     AND propose_date IS NOT NULL
     AND stage IS NOT NULL AND stage <> ''
     AND summary IS NOT NULL AND summary <> ''
    THEN 'READY'
    WHEN (bill_name IS NOT NULL AND bill_name <> '')
      OR propose_date IS NOT NULL
      OR (stage IS NOT NULL AND stage <> '')
      OR (summary IS NOT NULL AND summary <> '')
    THEN 'PARTIAL'
    ELSE 'PENDING'
END;

CREATE INDEX idx_bill_ingest_status_propose_date_id
    ON Bill (ingest_status, propose_date, bill_id);
