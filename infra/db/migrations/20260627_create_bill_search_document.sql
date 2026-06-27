CREATE TABLE IF NOT EXISTS BillSearchDocument (
    bill_id VARCHAR(255) NOT NULL,
    bill_name_text VARCHAR(255) NOT NULL,
    brief_summary_text TEXT NOT NULL,
    gpt_summary_text TEXT NOT NULL,
    raw_summary_text MEDIUMTEXT NOT NULL,
    search_text MEDIUMTEXT NOT NULL,
    source_modified_date DATETIME(6) NULL,
    rebuilt_date DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (bill_id),
    FULLTEXT KEY ft_bill_search_text (search_text),
    KEY idx_bill_search_document_source_modified_date (source_modified_date),
    CONSTRAINT fk_bill_search_document_bill
        FOREIGN KEY (bill_id) REFERENCES Bill (bill_id)
        ON DELETE CASCADE
);
