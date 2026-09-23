# Public API, Hooks, Commands, Config

## mod-mount-roulette

### C++ API (`MountRouletteMgr.h`, `sMountRouletteMgr`)
- `void LoadConfig()` — reads `MountRoulette.*`, called from `OnAfterConfigLoad`.
- `MountRouletteAccountState GetState(uint32 accountId)` — `{Spins, Shards, EpicPity, LegendaryPity}`.
- `void AddSpins(uint32 accountId, int32 amount, std::string const& reason, Player* contextPlayer = nullptr)`
  — adds/subtracts spins (clamped at 0), persists, logs to `mountroulette` channel.
- `MountRouletteSpinResult Spin(Player* player)` — level gate, `SpinCost` deduction,
  pity-aware rarity roll, reward grant (learn mount or duplicate shards). `Success == false`
  with `Error` set on rejection (disabled/level/no spins/no reward configured); refunds the
  spin cost on the last case.
- `MountRouletteSpinResult ForceReward(Player* player, uint32 spellId)` — GM path, same
  grant/duplicate/log logic as `Spin`, bypasses RNG/pity/spin cost.
- `static char const* RarityToString(MountRarity)`.

### Commands (SEC_GAMEMASTER)
- `.mroulette addspins <player> <amount>`
- `.mroulette info <player>`
- `.mroulette spin <player>` — target must be online (`learnSpell` needs a live `Player*`).
- `.mroulette reward <player> <spellId>` — target must be online.

### Config (`conf/mod_mount_roulette.conf.dist`)
- `MountRoulette.Enable` (default 1)
- `MountRoulette.RequiredLevel` (default 80) — enforced by `Spin()`.
- `MountRoulette.SpinCost` (default 1) — enforced by `Spin()`.
- `MountRoulette.Chance.<Common|Rare|Epic|Legendary|Mythic>` — basis points, must sum to 10000.
- `MountRoulette.Rewards.<Rarity>` — comma-separated spell IDs, empty by default (must be filled in).
- `MountRoulette.EpicPity` / `MountRoulette.LegendaryPity` (default 0 = disabled).
- `MountRoulette.DuplicateShards.<Rarity>` (default 0).
- `MountRoulette.ShardCost` (default 0, reserved — no spend mechanic implemented).
- `Appender.MountRoulette` / `Logger.mountroulette` — log channel to `MountRoulette.log`.

### Player addon bridge (Phase 4, `MountRouletteAddonBridge.cpp`) — no AIO

Uses AzerothCore's built-in `AddonChannelCommandHandler` (Chat.cpp) instead of
AIO/third-party code: the client addon issues these through the normal
`ChatHandler` command path (self-whisper, `CHAT_MSG_ADDON`, `"AzerothCore\t"`
wire format), so SEC_PLAYER checks apply exactly as for a typed command.
Structured results are pushed back as a raw `CHAT_MSG_ADDON` message under
prefix `MTRLT` (`"MTRLT\t<kind>|<field>|..."`), independent of the command's
human-readable chat output.

### Commands (SEC_PLAYER, self only, no target argument)
- `.roulette spin` — runs `Spin(player)`; sends `MTRLT` `SPIN_OK|rarity|spellId|dup|shards|spinsLeft|epicPity|legPity` or `SPIN_FAIL|error`.
- `.roulette info` — sends `MTRLT` `INFO|spins|shards|epicPity|legPity`.
- `.roulette collection` — sends `MTRLT` `COLLECTION|spellId,spellId,...`.
- All three reply `MTRLT` `DENY|level` (and no-op) when `player->GetLevel() < RequiredLevel`.

### Client addon (`client_addon/MountRoulette/`)
- `MountRoulette.toc` + `MountRoulette.lua`, Interface 30300 (3.3.5a), no dependencies.
- Sends `roulette spin|info|collection` via `SendAddonMessage("AzerothCore", "i"..counter..cmd, "WHISPER", UnitName("player"))`.
- Listens on `CHAT_MSG_ADDON` for prefix `MTRLT`, parses pipe-delimited payload into the window (spins/shards/pity/result/collection).
- `/mroulette` slash command toggles the window.
- **Manual one-time install**: copy `client_addon/MountRoulette/` into the player's `WoW_installation/Interface/AddOns/`. No server-side auto-delivery (that was AIO's only remaining role; dropped per decision below).

## mod-server-activities

### C++ API (`ServerActivitiesMgr.h`, `sServerActivitiesMgr`)
- `void LoadConfig()` — reads `ServerActivities.*`.
- `bool CreditActivity(Player* player, std::string const& activityId, uint32 spins, uint32 dailyLimit)`
  — level/bot gate, daily-limit check+increment, calls `MountRouletteMgr::AddSpins` on success.
- `void ResetDaily(Player*)` / `void ResetDaily(uint32 guidLow)` — deletes today's daily-limit row(s).

### Hooks used
- `AllBattlegroundScript::OnBattlegroundEndReward` (winner-only filter via `player->GetBgTeamId() == winnerTeamId`).
- `GlobalScript::OnAfterUpdateEncounterState` (Dungeon/Heroic, Phase 2).
- `PlayerScript::OnPlayerRewardKillRewarder` (Raid Boss, Phase 2).
- `PlayerScript::OnPlayerAchievementComplete` (Achievement, Phase 2).
- `PlayerScript::OnPlayerCanAreaExploreAndOutdoor` (Exploration, Phase 6) — read-only
  `PLAYER_EXPLORED_ZONES_1` bit check before core's own explore-flag write, so only a
  genuinely new area credits; always returns `true` (never blocks core exploration/XP).
- `PlayerScript::OnPlayerLootItem` (Profession, Fishing, Phase 6) — fires for any item
  actually taken from a lootable source (creature, gathering node, fishing catch);
  credit gated by a configured item-id allowlist, not by skill-up outcome, since
  `OnPlayerUpdateGatheringSkill`/`OnPlayerUpdateCraftingSkill` fire on every gather/craft
  attempt regardless of roll result or skill cap and carry no item id (confirmed by
  reading `Player::UpdateGatherSkill`/`UpdateCraftSkill`, `PlayerUpdates.cpp`).

### Commands (SEC_GAMEMASTER)
- `.mactivity reset <player>`

### Config (`conf/mod_server_activities.conf.dist`)
- `ServerActivities.Enable` (default 1)
- `ServerActivities.RequiredLevel` (default 80)
- `ServerActivities.ResetHour` (default 0)
- `ServerActivities.BG.Enable` / `.Spins` / `.DailyLimit` (defaults 1/1/1)
- `ServerActivities.Dungeon.*` / `.Heroic.*` / `.Raid.*` / `.Achievement.*` (Phase 2, same shape)
- `ServerActivities.WorldEvent.Spins` / `.DailyLimit` (Phase 5, credited by mod-world-events)
- `ServerActivities.WorldBoss.Spins` / `.DailyLimit` (Phase 5, credited by mod-world-events)
- `ServerActivities.Exploration.Enable` / `.Spins` / `.DailyLimit` (Phase 6, defaults 1/1/1)
- `ServerActivities.Profession.Enable` / `.Spins` / `.DailyLimit` / `.ItemIDs` (Phase 6,
  `.ItemIDs` comma-separated item entries, empty by default)
- `ServerActivities.Fishing.Enable` / `.Spins` / `.DailyLimit` / `.ItemIDs` (Phase 6, same shape)

## mod-world-events

### C++ API (`WorldEventsMgr.h`, `sWorldEventsMgr`)
- `void LoadConfig()` — reads `WorldEvents.*`.
- `void Update(uint32 diff)` — called every world tick from `WorldScript::OnUpdate`;
  checks only the tracked-summon list for the active stage (no per-tick map scan).
- `bool StartEvent(std::string const& eventId, std::string& outMessage)` /
  `bool StopEvent(std::string const& eventId, std::string& outMessage)` — only
  `eventId == "invasion"` is implemented.
- `void OnBossKillCredited(Player*)` — called from the kill-rewarder hook while
  the Boss stage is active; credits `"worldevent"` and `"worldboss"` via
  `ServerActivitiesMgr::CreditActivity`.
- `void OnMapDestroyed(uint32 mapId)` — called from `AllMapScript::OnDestroyMap`;
  resets state if the invasion's own map is destroyed.

### Hooks used
- `WorldScript::OnUpdate` — stage-advance ticking + random auto-start accumulator.
- `AllMapScript::OnDestroyMap` — cleanup on map unload (not `WorldMapScript`,
  since the invasion map id is config-driven, not known at script-construction time).
- `PlayerScript::OnPlayerRewardKillRewarder` — boss kill credit, filtered by
  configured boss entry and active Boss stage (participation/proximity already
  resolved by core `KillRewarder`, same pattern as the Raid Boss activity).

### Commands (SEC_GAMEMASTER)
- `.mevent start invasion`
- `.mevent stop invasion`

### Config (`conf/mod_world_events.conf.dist`)
- `WorldEvents.Enable` (default 1)
- `WorldEvents.Invasion.MapId` / `.X` / `.Y` / `.Z` / `.O` / `.SpawnRadius` — spawn point (all default 0/15)
- `WorldEvents.Invasion.WaveEntry` / `.WaveCount` / `.WaveCreatureCount` / `.WaveTimeoutSeconds`
- `WorldEvents.Invasion.EliteEntry` / `.EliteCount` / `.EliteTimeoutSeconds`
- `WorldEvents.Invasion.BossEntry` / `.BossTimeoutSeconds`
- `WorldEvents.Invasion.RandomStart.Enable` / `.IntervalSeconds` / `.ChancePercent` — optional
  auto-start roll while idle (default disabled)
- `WaveEntry`/`EliteEntry`/`BossEntry` default to `0` (disabled) — **must be filled in with real
  creature entries before `.mevent start invasion` will do anything** (same
  empty-by-default pattern as `MountRoulette.Rewards.<Rarity>` in Phase 3).

## Phase 7.1 (mod-world-events — generic framework + City Defense)

### `WorldEventRegistry` (`WorldEventRegistry.h`)
- `void Register(std::string id, Factory)` — adds an event type. Called once
  per event type via a static registrar object in that event's `.cpp`
  (see `Events/CityDefenseEvent.cpp`).
- `std::unique_ptr<WorldEvent> Create(std::string id)` — factory lookup.
- `bool Contains(std::string id)`, `std::vector<std::string> GetRegisteredIds()`.

### `WorldEvent` (`WorldEvent.h`) — base class for a registry event
Public: `Start()/Update(diff)/Stop(graceful)`, `NotifyCreatureKilled(killer, victim)`,
`NotifyPlayerEnter(player)`, `ForceComplete(player)`, `ResetDailyLimitFor(accountId)`,
`ReloadConfig()`, `GetId()/GetState()/GetMapId()/GetLastBotDispatch()`.
Protected (for subclasses): `OnStart/OnUpdate/OnStop/OnCreatureKilled/OnPlayerEnter`,
`OnSuccess/OnFailure` (called once, exactly when `IsCompleted()`/`IsFailed()` first
go true), `IsCompleted()/IsFailed()` (pure-ish, default false),
`RegisterParticipant(player)` (bots silently ignored), `FilterParticipants(predicate)`,
`GrantRewardsToParticipants(type, amount, dailyLimit, requiredLevel)`,
`SendBotsToEvent(mapId, pos, maxParticipants, minLevel, balanceRoles)`, `Announce(text)`.

### `RewardMgr` (`RewardMgr.h`)
- `RewardMgr::RewardPlayer(Player*, RewardType, amount, source, itemId = 0)` —
  `RewardType::{Spin, Shards, Gold, Item}`. `Spin` calls
  `MountRouletteMgr::AddSpins`; `Shards` is currently a logged no-op (no
  event needs it yet — see decisions.md).
- `RewardType RewardTypeFromString(std::string, fallback = Spin)` — parses
  the `*.Reward.Type` config key.

### `WorldEventsMgr` additions
- `void OnPlayerCreatureKilled(Player*, Creature*)` — dispatches to the
  active registry event (invasion has its own separate boss-kill hook).
- `std::string GetActiveEventId() const` / `WorldEventState GetActiveEventState() const`.
- `std::vector<std::string> ListKnownEventIds() const` — registry ids + `"invasion"`.
- `bool ResetPlayerDaily(playerName, eventId, outMessage)` — works offline
  (resolves account id via `CharacterCache`).
- `bool ForceCompleteEvent(playerName, eventId, outMessage)` — player must be
  online; routes through `WorldEvent::ForceComplete` → `OnSuccess()` → `RewardMgr`.
- `std::vector<std::pair<std::string,uint32>> GetPlayerDailyStatus(playerName) const`.
- `StartEvent`/`StopEvent` now branch: `eventId == "invasion"` keeps the exact
  Phase 5 path; any other id goes through `WorldEventRegistry` +
  `WorldEventsMgr::_active` (`WorldEvents.MaxConcurrentEvents` caps concurrency
  across both paths combined).

### Hooks used (new)
- `PlayerScript::OnPlayerCreatureKill` (`WorldEventsParticipantScript.cpp`) —
  feeds every player creature kill to the active generic event.

### Commands (SEC_GAMEMASTER)
- `.mevent start <id>` / `.mevent stop [id]` (id optional on stop — defaults to
  whatever is currently active)
- `.mevent list` — known event ids
- `.mevent active` — currently active event id + state
- `.mevent info <player>` — today's per-event completion counts for that
  player's account
- `.mevent reset <player> [event]` — clears today's daily-limit row(s), offline OK
- `.mevent complete <player> <event>` — forces success + reward, bypasses objectives
- `.mevent debug on|off`
- `.mevent bots` — last dispatch's selected/travelling bot counts

### Config (`conf/mod_world_events.conf.dist`, Phase 7.1 additions)
- `WorldEvents.MaxConcurrentEvents` (default 1)
- `WorldEvents.Playerbots.Enabled` / `.MaxParticipants` / `.MinLevel` / `.TravelImmediately`
- `WorldEvents.CityDefense.MapId` / `.X` / `.Y` / `.Z` / `.O` / `.Radius`
- `WorldEvents.CityDefense.CaptainEntry` / `.InvaderEntry` / `.EliteEntry` / `.CommanderEntry`
  (default to the spec's reserved range 910700-910703 — **no matching
  `creature_template` rows exist yet**, see phase-status.md)
- `WorldEvents.CityDefense.TimeoutMinutes` (default 15)
- `WorldEvents.CityDefense.Reward.Type` / `.Reward.Amount` / `.DailyLimit`
  (default SPIN / 2 / 1)

## Phase 7.2 (mod-world-events — Caravan / World Boss / Rare Hunt / Bounty Hunt)

### `WorldEvent` addition
- `void OnKillRewarded(Player*, Creature*)` (protected, overridable) /
  `void NotifyKillRewarded(Player*, Creature*)` (public, called by
  `WorldEventsMgr`) — fed from `PLAYERHOOK_ON_REWARD_KILL_REWARDER`
  instead of the plain per-kill hook, for events needing core's own
  raid/group credit resolution (`RandomWorldBossEvent` is the only user
  so far).

### `WorldEventsMgr` addition
- `void OnPlayerKillRewarded(Player*, Creature*)` — dispatches to the
  active event's `NotifyKillRewarded`.

### Hooks used (new)
- `PlayerScript::OnPlayerRewardKillRewarder` (`WorldEventsParticipantScript.cpp`,
  alongside its existing `OnPlayerCreatureKill`) — relays core's
  `KillRewarder` credit resolution.

### New registry events (no command/GM-surface changes — see Phase 7.1's registry)
- `"caravan"` (`CaravanEscortEvent`), `"worldboss"` (`RandomWorldBossEvent`),
  `"rarehunt"` (`RareHuntEvent`), `"bounty"` (`BountyHuntEvent`).

### Config (`conf/mod_world_events.conf.dist`, Phase 7.2 additions)
- `WorldEvents.Caravan.MapId/StartX/Y/Z/O/DestX/Y/Z`, `.CaravanEntry/.AmbusherEntry/.RaiderEntry/.RaidLeaderEntry`, `.AmbushSize`, `.TimeoutMinutes`, `.Reward.*`, `.DailyLimit`
- `WorldEvents.WorldBoss.MapId/X/Y/Z/O/Radius`, `.Entry`, `.BaseHealth/.HealthPerExtraPlayerPct/.MaxHealthMultiplier`, `.RescaleIntervalSeconds`, `.TimeoutMinutes`, `.Reward.*`, `.DailyLimit`
- `WorldEvents.RareHunt.MapId`, `.SpawnPoints` (`"x,y,z|x,y,z|..."`), `.Entry/.Health`, `.TimeoutMinutes`, `.Reward.*`, `.DailyLimit`
- `WorldEvents.BountyHunt.MapId`, `.TargetAEntry/BEntry/CEntry`, `.Target{A,B,C}.X/Y/Z`, `.TimeoutMinutes`, `.Reward.*`, `.DailyLimit`
- All 9 new creature entries (910710-910713, 910720, 910730, 910740-910742)
  default to the spec's reserved range — **no matching `creature_template`
  rows exist yet**, same gap as Phase 7.1's City Defense.

## Phase 7.4 (mod-world-events — Server Wide / Corrupted Zone / Dungeon Event / Fishing Frenzy / World PvP)

### `WorldEvent` additions
- `OnCreatureSpawned(Creature*)` / `NotifyCreatureSpawned(Creature*)` — fed
  from `AllCreatureScript::OnCreatureAddWorld` (per-spawn, server-wide).
- `OnDungeonCompleted(Map*)` / `NotifyDungeonCompleted(Map*)` — fed from a
  dedicated `GlobalScript::OnAfterUpdateEncounterState` hook, independent
  of mod-server-activities' own dungeon credit.
- `OnFishingAttempt(Player*)` / `NotifyFishingAttempt(Player*)` — fed from
  `PLAYERHOOK_ON_UPDATE_FISHING_SKILL`.
- `OnPvpKill(Player* killer, Player* killed)` / `NotifyPvpKill(...)` — fed
  from `PLAYERHOOK_ON_PVP_KILL`.
- `OnGossipAction(Player*, uint32 actionCode)` / `NotifyGossipAction(...)`
  — fed from a gossip-menu `CreatureScript`.

### `WorldEventsMgr` additions
- `OnCreatureSpawnedAnywhere`, `OnDungeonRunCompleted`,
  `OnPlayerFishingAttempt`, `OnPlayerPvpKill`, `OnPlayerGossipAction` —
  each dispatches to the active event's matching `Notify*`.

### Hooks used (new)
- `AllCreatureScript::OnCreatureAddWorld` (`WorldEventsZoneModifierScript.cpp`)
- `GlobalScript::OnAfterUpdateEncounterState` (`WorldEventsDungeonScript.cpp`)
- `PlayerScript::OnPlayerUpdateFishingSkill`, `OnPlayerPVPKill` (added to `WorldEventsParticipantScript.cpp`)
- `CreatureScript::OnGossipHello`/`OnGossipSelect` (`WorldEventsQuartermasterScript.cpp`, ScriptName `npc_war_effort_quartermaster`)

### New registry events
- `"serverwide"` (`ServerWideEventEvent`), `"corruptedzone"`
  (`CorruptedZoneEvent`), `"dungeonevent"` (`DungeonEventEvent`),
  `"fishing"` (`FishingFrenzyEvent`), `"worldpvp"` (`WorldPvpEventEvent`).

### Config (`conf/mod_world_events.conf.dist`, Phase 7.4 additions)
- `WorldEvents.ServerWide.ItemIDs/.PersonalGoal/.ServerGoal/.DurationMinutes/.Reward.*/.DailyLimit`
- `WorldEvents.CorruptedZone.ZoneId/.HealthMultiplier/.DamageMultiplier/.MinCreatureLevel/.RequiredKills/.DurationMinutes/.Reward.*/.DailyLimit` (`ZoneId` defaults to `0`/disabled — unconfirmed zone id, see decisions.md)
- `WorldEvents.DungeonEvent.MapIds` (default `575,602,578,595,604` — verified against this repo's `mod-dungeon-clear`), `.HealthMultiplier/.DamageMultiplier/.AllowActivityRewardStacking/.DurationMinutes/.Reward.*/.DailyLimit`
- `WorldEvents.FishingFrenzy.ZoneId` (default `0`/disabled, same reason as CorruptedZone), `.FishItemId/.EventFishChancePct/.RequiredFish/.DurationMinutes/.Reward.*/.DailyLimit`
- `WorldEvents.WorldPvP.MapId/X/Y/Z/Radius/.RequiredUniqueKills/.MinRealParticipants/.DurationMinutes/.Reward.*/.DailyLimit`

## Phase 7.3 (mod-world-events — Portal Event / Treasure Hunt / Resource Rush)

### `WorldEvent` additions
- `void OnItemLooted(Player*, ObjectGuid lootSourceGuid)` (protected,
  overridable) / `void NotifyItemLooted(Player*, ObjectGuid)` (public,
  called by `WorldEventsMgr`) — fed from `PLAYERHOOK_ON_LOOT_ITEM`;
  `lootSourceGuid` is whatever was looted from (creature or gameobject).
- `bool TryRewardPlayer(Player*, RewardType, amount, dailyLimit, requiredLevel)`
  — immediate level+daily-limit+grant check for one player/one action,
  returns whether it granted. `GrantRewardsToParticipants` now calls this
  per participant internally.

### `WorldEventsMgr` addition
- `void OnPlayerItemLooted(Player*, ObjectGuid)` — dispatches to the active
  event's `NotifyItemLooted`.

### Hooks used (new)
- `PlayerScript::OnPlayerLootItem` (`WorldEventsParticipantScript.cpp`,
  alongside its existing kill hooks) — relays every player loot event.

### New registry events
- `"portal"` (`PortalEventEvent`), `"treasure"` (`TreasureHuntEvent`,
  rewards per chest via `TryRewardPlayer`, not `GrantRewardsToParticipants`),
  `"resourcerush"` (`ResourceRushEvent`, same — rewards per hand-in;
  `IsCompleted()` always `false`, the event just runs for `DurationMinutes`).

### Config (`conf/mod_world_events.conf.dist`, Phase 7.3 additions)
- `WorldEvents.PortalEvent.MapId/X/Y/Z/O/Radius`, `.PortalGoEntry/.CreatureEntry/.EliteEntry/.BossEntry`, `.TimeoutMinutes`, `.Reward.*`, `.DailyLimit`
- `WorldEvents.TreasureHunt.MapId`, `.Points` (`"x,y,z|x,y,z|..."`), `.ChestEntry`, `.TimeoutMinutes`, `.Reward.*`, `.DailyLimit`
- `WorldEvents.ResourceRush.MapId/X/Y/Z/Radius`, `.NodeEntry/.FragmentItemId`, `.NodeCount`, `.RequiredFragments`, `.NodeRespawnSeconds`, `.DurationMinutes`, `.Reward.*`, `.DailyLimit`
- New entries 910750-910753 (Portal), 910760 (Treasure chest GO),
  910770/920770 (Resource Rush node GO / item) — **no `creature_template`/
  `gameobject_template`/`item_template`/`gameobject_loot_template` rows
  exist yet**, same gap as Phase 7.1/7.2.
