-- BOOT-8: persisted validation gate for mod_auction_bootstrap_run.
-- HandleResumeTrading (AuctionBootstrapMgr) refuses Validating ->
-- TradingResumed unless validation_passed = 1 for THIS run - never inferred
-- from state alone, and re-checked fresh after every worldserver restart
-- since these are real persisted DB columns, not an in-memory session flag.
-- Plain ADD COLUMN (not DROP+CREATE) - this table already holds a real,
-- in-progress bootstrap run's live data.
ALTER TABLE `mod_auction_bootstrap_run`
    ADD COLUMN `validation_passed` TINYINT UNSIGNED NOT NULL DEFAULT 0 AFTER `error_message`,
    ADD COLUMN `validated_at` INT UNSIGNED NULL DEFAULT NULL AFTER `validation_passed`,
    ADD COLUMN `validation_summary` TEXT NULL DEFAULT NULL AFTER `validated_at`;
