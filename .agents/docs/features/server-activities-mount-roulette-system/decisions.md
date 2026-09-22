# Technical Decisions

- **Storage: `characters` DB**, not `auth`, for account-scoped spins/shards/pity
  (open question #9 in the plan; used as-is, not yet confirmed by user).
- **Lazy daily limit**, not a scheduled reset job: `day_key` is derived from
  `GameTime::GetGameTime()` shifted by `ServerActivities.ResetHour` hours
  (`(now - resetHour*3600) / 86400`), no periodic task or bulk UPDATE.
- **In-memory account cache** (`unordered_map<accountId, state>`) in
  `MountRouletteMgr`, loaded on first access, saved synchronously on every
  `AddSpins`. No TTL/eviction yet — acceptable at tracer-bullet scale, revisit
  if account count becomes large.
- **Bot exclusion**: `CreditActivity` returns `false` for `GET_PLAYERBOT_AI(player) != nullptr`
  under `#ifdef MOD_PLAYERBOTS`, matching the existing codebase pattern (see
  `modules/mod-ai-director`). No BOT_BOT observer logic applies here — this
  feature is player-only, not a bot-bot interaction.
- **Command surface split**: `.mroulette info` (shows spins/shards/pity and,
  via a plain read-only SELECT, today's `mod_server_activities_daily` rows)
  lives in mod-mount-roulette to keep the dependency direction one-way
  (server-activities → mount-roulette); it does not call into
  `ServerActivitiesMgr`.
- **Activity Manager as a thin class**, not a generic registry/plugin system:
  `ServerActivitiesMgr::CreditActivity(player, activityId, spins, dailyLimit)`
  is a single reusable entry point; per-activity scripts (e.g. the BG script)
  call it directly with their own config values. No abstraction for
  not-yet-implemented activity types was added.
