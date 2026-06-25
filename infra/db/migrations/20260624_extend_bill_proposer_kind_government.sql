-- Allow government-submitted bills to be stored without rewriting them as congressman bills.
-- MySQL 8.0.35 requires the default COPY path for this enum modification, so keep
-- this migration isolated from row updates or index creation.

ALTER TABLE Bill
    MODIFY COLUMN proposer_kind ENUM('CHAIRMAN', 'CONGRESSMAN', 'GOVERNMENT') DEFAULT 'CONGRESSMAN';
