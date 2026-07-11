CREATE TABLE IF NOT EXISTS BillReportTooltip (
    bill_id VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
    source_report_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    rendered_summary TEXT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    applied_count SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    attempt_count INT UNSIGNED NOT NULL DEFAULT 0,
    model_name VARCHAR(64) NULL,
    last_error TEXT NULL,
    claimed_at DATETIME(6) NULL,
    processed_at DATETIME(6) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (bill_id),
    KEY idx_bill_report_tooltip_status_claimed (status, claimed_at),
    KEY idx_bill_report_tooltip_updated_at (updated_at),
    CONSTRAINT chk_bill_report_tooltip_status
        CHECK (status IN ('PENDING', 'RUNNING', 'APPLIED', 'SKIPPED', 'FAILED')),
    CONSTRAINT fk_bill_report_tooltip_bill
        FOREIGN KEY (bill_id) REFERENCES Bill (bill_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
