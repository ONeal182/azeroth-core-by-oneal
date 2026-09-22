# Database

Both tables live in `characters`. Base-creation SQL only (no update migrations yet).

## `mod_mount_roulette_account`
File: `modules/mod-mount-roulette/data/sql/db-characters/b_mod_mount_roulette_account.sql`

| Column | Type | Notes |
|---|---|---|
| account_id | INT UNSIGNED, PK | |
| spins | INT UNSIGNED, default 0 | balance spent on roulette (Phase 3) |
| shards | INT UNSIGNED, default 0 | unused until Phase 3 |
| epic_pity | INT UNSIGNED, default 0 | unused until Phase 3 |
| legendary_pity | INT UNSIGNED, default 0 | unused until Phase 3 |

## `mod_server_activities_daily`
File: `modules/mod-server-activities/data/sql/db-characters/b_mod_server_activities_daily.sql`

| Column | Type | Notes |
|---|---|---|
| guid | INT UNSIGNED | character guid low part |
| activity_id | VARCHAR(32) | e.g. `"bg"` |
| day_key | INT UNSIGNED | `(now - ResetHour*3600) / 86400` |
| count | SMALLINT UNSIGNED, default 0 | times credited today |

PK: (guid, activity_id, day_key).

## Not yet created
- `mod_mount_roulette_collection` (account_id, spell_id) — Phase 3.
