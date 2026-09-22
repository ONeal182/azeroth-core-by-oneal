# Public API, Hooks, Commands, Config

## mod-mount-roulette

### C++ API (`MountRouletteMgr.h`, `sMountRouletteMgr`)
- `void LoadConfig()` — reads `MountRoulette.*`, called from `OnAfterConfigLoad`.
- `MountRouletteAccountState GetState(uint32 accountId)` — `{Spins, Shards, EpicPity, LegendaryPity}`.
- `void AddSpins(uint32 accountId, int32 amount, std::string const& reason, Player* contextPlayer = nullptr)`
  — adds/subtracts spins (clamped at 0), persists, logs to `mountroulette` channel.

### Commands (SEC_GAMEMASTER)
- `.mroulette addspins <player> <amount>`
- `.mroulette info <player>`

### Config (`conf/mod_mount_roulette.conf.dist`)
- `MountRoulette.Enable` (default 1)
- `MountRoulette.RequiredLevel` (default 80) — read, not yet enforced by any Phase 1 code path.
- `MountRoulette.SpinCost` (default 1) — reserved for Phase 3.
- `Appender.MountRoulette` / `Logger.mountroulette` — log channel to `MountRoulette.log`.

## mod-server-activities

### C++ API (`ServerActivitiesMgr.h`, `sServerActivitiesMgr`)
- `void LoadConfig()` — reads `ServerActivities.*`.
- `bool CreditActivity(Player* player, std::string const& activityId, uint32 spins, uint32 dailyLimit)`
  — level/bot gate, daily-limit check+increment, calls `MountRouletteMgr::AddSpins` on success.
- `void ResetDaily(Player*)` / `void ResetDaily(uint32 guidLow)` — deletes today's daily-limit row(s).

### Hooks used
- `AllBattlegroundScript::OnBattlegroundEndReward` (winner-only filter via `player->GetBgTeamId() == winnerTeamId`).

### Commands (SEC_GAMEMASTER)
- `.mactivity reset <player>`

### Config (`conf/mod_server_activities.conf.dist`)
- `ServerActivities.Enable` (default 1)
- `ServerActivities.RequiredLevel` (default 80)
- `ServerActivities.ResetHour` (default 0)
- `ServerActivities.BG.Enable` / `.Spins` / `.DailyLimit` (defaults 1/1/1)
