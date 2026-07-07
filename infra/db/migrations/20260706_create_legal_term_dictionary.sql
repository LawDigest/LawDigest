CREATE TABLE IF NOT EXISTS LegalTermDictionary (
    term_id BIGINT NOT NULL AUTO_INCREMENT,
    source VARCHAR(32) NOT NULL DEFAULT 'law.go.kr',
    source_term_id TEXT NULL,
    term VARCHAR(255) NOT NULL,
    normalized_term VARCHAR(255) NOT NULL,
    definition TEXT NOT NULL,
    definition_sources JSON NULL,
    raw_payload JSON NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_synced_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (term_id),
    UNIQUE KEY uq_legal_term_dictionary_source_normalized_term (source, normalized_term),
    KEY idx_legal_term_dictionary_enabled_term (enabled, normalized_term)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
