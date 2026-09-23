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

## `mod_mount_roulette_collection`
File: `modules/mod-mount-roulette/data/sql/db-characters/b_mod_mount_roulette_collection.sql`

| Column | Type | Notes |
|---|---|---|
| account_id | INT UNSIGNED | account-scoped, not per-character |
| spell_id | INT UNSIGNED | learned mount spell |

PK: (account_id, spell_id). Rows inserted via `INSERT IGNORE` on a non-duplicate spin/reward.

## Phase 5 (mod-world-events)

No new tables. Boss-kill credit reuses `mod_server_activities_daily` via
`ServerActivitiesMgr::CreditActivity` with activity ids `"worldevent"` and
`"worldboss"` — same table, no schema change.

## `mod_world_events_daily` (Phase 7.1)
File: `modules/mod-world-events/data/sql/db-characters/b_mod_world_events_daily.sql`

| Column | Type | Notes |
|---|---|---|
| account_id | INT UNSIGNED | account-scoped (not per-character — spec §11) |
| event_id | VARCHAR(32) | registry id, e.g. `"citydefense"` |
| day_key | INT UNSIGNED | `(now - ResetHour*3600) / 86400`, same formula as `mod_server_activities_daily` |
| count | SMALLINT UNSIGNED, default 0 | times rewarded today |

PK: (account_id, event_id, day_key). Separate table from
`mod_server_activities_daily` because that one is keyed by character `guid`
(per-character, Phases 1-6); reusing it with an account id in the `guid`
column would silently change its meaning for every existing activity.
