-- mod-playerbot-auction-ai: Auction Bootstrap (BOOT-1) persistence tables.
-- Tracks a one-time, resumable, crash-safe market reset/seed operation
-- (see AuctionBootstrapMgr). Never touched by ordinary Auction AI code -
-- these three tables exist only while a bootstrap run is prepared/in
-- progress/being reviewed; they never feed back into normal buy/sell logic.

DROP TABLE IF EXISTS `mod_auction_bootstrap_run`;
CREATE TABLE `mod_auction_bootstrap_run` (
    `run_id` VARCHAR(64) NOT NULL,
    `json_hash` CHAR(64) NOT NULL,
    `seed` BIGINT NOT NULL,
    `dry_run` TINYINT(1) UNSIGNED NOT NULL DEFAULT 0,
    `state` VARCHAR(32) NOT NULL DEFAULT 'PREPARED',
    `total_old_auctions` INT UNSIGNED NOT NULL DEFAULT 0,
    `old_auctions_processed` INT UNSIGNED NOT NULL DEFAULT 0,
    `total_planned_lots` INT UNSIGNED NOT NULL DEFAULT 0,
    `new_lots_created` INT UNSIGNED NOT NULL DEFAULT 0,
    `backup_confirmed_path` VARCHAR(512) NULL DEFAULT NULL,
    `error_message` TEXT NULL DEFAULT NULL,
    `created_at` INT UNSIGNED NOT NULL DEFAULT 0,
    `updated_at` INT UNSIGNED NOT NULL DEFAULT 0,
    PRIMARY KEY (`run_id`) USING BTREE
)
CHARSET = utf8mb4
COLLATE = utf8mb4_unicode_ci
ENGINE = InnoDB
ROW_FORMAT = DEFAULT
;

-- One row per LEGACY auction snapshotted before cancellation - doubles as
-- the deletion manifest and the idempotency/crash-recovery ledger.
-- status: PENDING -> CANCELLING -> CANCELLED, or -> SKIPPED_UNSAFE.
-- execution_token/started_at let a resumed run tell "attempted, unknown
-- outcome, must re-check the real auctionhouse/mail before deciding" apart
-- from "never touched yet".
DROP TABLE IF EXISTS `mod_auction_bootstrap_old_auction`;
CREATE TABLE `mod_auction_bootstrap_old_auction` (
    `run_id` VARCHAR(64) NOT NULL,
    `auction_id` INT UNSIGNED NOT NULL,
    `houseid` TINYINT UNSIGNED NOT NULL DEFAULT 0,
    `item_template` INT UNSIGNED NOT NULL DEFAULT 0,
    `item_count` INT UNSIGNED NOT NULL DEFAULT 0,
    `owner_guid` INT UNSIGNED NOT NULL DEFAULT 0,
    `bidder_guid` INT UNSIGNED NOT NULL DEFAULT 0,
    `bid` INT UNSIGNED NOT NULL DEFAULT 0,
    `buyout` INT UNSIGNED NOT NULL DEFAULT 0,
    `deposit` INT UNSIGNED NOT NULL DEFAULT 0,
    `expire_time` INT UNSIGNED NOT NULL DEFAULT 0,
    `status` VARCHAR(16) NOT NULL DEFAULT 'PENDING',
    `execution_token` VARCHAR(64) NULL DEFAULT NULL,
    `started_at` INT UNSIGNED NULL DEFAULT NULL,
    `processed_at` INT UNSIGNED NULL DEFAULT NULL,
    `error_message` TEXT NULL DEFAULT NULL,
    PRIMARY KEY (`run_id`, `auction_id`) USING BTREE,
    INDEX `idx_run_status` (`run_id`, `status`) USING BTREE
)
CHARSET = utf8mb4
COLLATE = utf8mb4_unicode_ci
ENGINE = InnoDB
ROW_FORMAT = DEFAULT
;

-- One row per PLANNED new lot (written by the offline Python planner as
-- status=PLANNED; everything else is filled in by the C++ executor).
-- status: PLANNED -> CREATING -> CREATED, or -> FAILED.
-- created_item_guid/created_auction_id are filled in the SAME DB
-- transaction as the real item_instance/auctionhouse rows (see
-- AuctionBootstrapSeeder), so a crash mid-transaction rolls all three back
-- together; execution_token/started_at exist as a defense-in-depth check on
-- resume (reconcile against the real live tables before trusting `status`).
DROP TABLE IF EXISTS `mod_auction_bootstrap_new_lot`;
CREATE TABLE `mod_auction_bootstrap_new_lot` (
    `run_id` VARCHAR(64) NOT NULL,
    `lot_id` VARCHAR(64) NOT NULL,
    `item_id` INT UNSIGNED NOT NULL,
    `stack_size` INT UNSIGNED NOT NULL,
    `buyout` INT UNSIGNED NOT NULL,
    `startbid` INT UNSIGNED NOT NULL,
    `duration_seconds` INT UNSIGNED NOT NULL,
    `original_reference_price` INT UNSIGNED NOT NULL,
    `effective_reference_price` INT UNSIGNED NOT NULL,
    `price_adjust_reason` VARCHAR(32) NULL DEFAULT NULL,
    `seller_guid` INT UNSIGNED NOT NULL,
    `houseid` TINYINT UNSIGNED NOT NULL,
    `status` VARCHAR(16) NOT NULL DEFAULT 'PLANNED',
    `execution_token` VARCHAR(64) NULL DEFAULT NULL,
    `started_at` INT UNSIGNED NULL DEFAULT NULL,
    `created_item_guid` INT UNSIGNED NULL DEFAULT NULL,
    `created_auction_id` INT UNSIGNED NULL DEFAULT NULL,
    `created_at` INT UNSIGNED NULL DEFAULT NULL,
    `error_message` TEXT NULL DEFAULT NULL,
    PRIMARY KEY (`run_id`, `lot_id`) USING BTREE,
    INDEX `idx_run_status` (`run_id`, `status`) USING BTREE,
    INDEX `idx_run_item` (`run_id`, `item_id`) USING BTREE
)
CHARSET = utf8mb4
COLLATE = utf8mb4_unicode_ci
ENGINE = InnoDB
ROW_FORMAT = DEFAULT
;
