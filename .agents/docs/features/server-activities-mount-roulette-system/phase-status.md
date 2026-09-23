# Phase Status

## Phase 1 — Tracer bullet: BG victory grants spins

**Status:** Implemented, **NOT VERIFIED** (no build/runtime performed per user instruction for this session).

Implemented:
- Module skeletons `mod-mount-roulette`, `mod-server-activities` (conf, loader, WorldScript config load).
- `MountRouletteMgr` (spins/shards/pity cache + persistence, `AddSpins`, `GetState`).
- `ServerActivitiesMgr` (level/bot gate, lazy daily-limit via `day_key`, `CreditActivity`, `ResetDaily`).
- Battleground Victory activity via `AllBattlegroundScript::OnBattlegroundEndReward`, winner-only.
- Commands: `.mroulette addspins`, `.mroulette info`, `.mactivity reset`.
- `MountRoulette.log` channel (`Appender.MountRoulette` / `Logger.mountroulette`) with LOG_INFO lines in `MountRouletteMgr::AddSpins` and `ServerActivitiesMgr::CreditActivity`.

Not done in this phase (by design — later phases):
- Dungeon/Heroic/Raid/Achievement activities (Phase 2).
- Roulette spin backend, RNG, pity, mount collection table (Phase 3).
- AIO UI (Phase 4).
- World events (Phase 5+).

## Phase 2 — PvE and Achievement activities

**Status:** Implemented, build PASS. Runtime/gameplay and DB/log verification NOT VERIFIED (no worldserver run performed this session).

Implemented:
- `ServerActivitiesDungeonScript` (`GlobalScript::OnAfterUpdateEncounterState`): credits `dungeon` or `heroic` activity id to every player on a non-raid dungeon map when `dungeonCompleted != 0`; type resolved via `Map::IsHeroic()`.
- `ServerActivitiesRaidScript` (`PlayerScript::OnPlayerRewardKillRewarder`): credits `raidboss` when the rewarded player is on a raid map (`Map::IsRaid()`) and the kill-rewarder victim is `Creature::IsDungeonBoss()`; participation/proximity already resolved by core `KillRewarder`.
- `ServerActivitiesAchievementScript` (`PlayerScript::OnPlayerAchievementComplete`): credits `achievement` for any completed achievement (no id filter, per plan note).
- All three route through the existing `ServerActivitiesMgr::CreditActivity` entry point (level/bot gate, lazy daily-limit, spin credit) — no new manager/scheduler added.
- Config: `ServerActivities.Dungeon.*`, `ServerActivities.Heroic.*`, `ServerActivities.Raid.*`, `ServerActivities.Achievement.*` (`Enable`, `Spins`, `DailyLimit`) added to `mod_server_activities.conf.dist`.
- `.mroulette info` already lists `mod_server_activities_daily` rows generically by `activity_id` — no code change needed for new activities to appear.
- Loader: `sa_loader.cpp` registers the three new scripts.

**Files changed:**
- `modules/mod-server-activities/src/ServerActivitiesDungeonScript.cpp` (new)
- `modules/mod-server-activities/src/ServerActivitiesRaidScript.cpp` (new)
- `modules/mod-server-activities/src/ServerActivitiesAchievementScript.cpp` (new)
- `modules/mod-server-activities/src/sa_loader.cpp`
- `modules/mod-server-activities/conf/mod_server_activities.conf.dist`

**Verification:**
- build — PASS (`cmake --build . --target worldserver --config RelWithDebInfo`, exit 0, `worldserver.exe` linked).
- runtime/gameplay (normal+heroic dungeon clear, raid boss kill in/out of raid group, achievement grant) — NOT VERIFIED.
- DB/log verification (`mod_server_activities_daily` rows, `MountRoulette.log` lines) — NOT VERIFIED.

**Known limitations:** Achievement activity has no per-ID filter (matches plan's "optional, only if needed" note — left open per PRD). Raid Boss activity does not yet distinguish "world boss" (Phase 5 scope).

## Phase 3 — Mount Roulette backend

**Status:** Implemented, build PASS. Runtime/gameplay and DB/log verification NOT VERIFIED (no worldserver run performed this session).

Implemented:
- `MountRouletteMgr::Spin(Player*)`: level gate, `SpinCost` deduction, pity-aware rarity roll (`RollRarity` via `urand(1,10000)` against `Chance.*` cumulative basis points), reward resolution, refunds the spin if the rolled rarity has no configured reward spell.
- Pity: `LegendaryPity`/`EpicPity` counters increment per non-qualifying spin and force the next spin to at least that rarity once the configured threshold is reached; hitting Epic-or-above resets `epic_pity`, hitting Legendary resets `legendary_pity` too.
- Reward grant (`GrantReward`): duplicate check against `mod_mount_roulette_collection` (account-scoped, not per-character); new spell → `INSERT IGNORE` into collection + `Player::learnSpell`; duplicate → `DuplicateShards.<Rarity>` added to shard balance instead. Spins/shards/pity persisted via existing `Save()` (`REPLACE INTO mod_mount_roulette_account`).
- `MountRouletteMgr::ForceReward(Player*, spellId)`: GM-forced reward path reusing the same duplicate/collection/log logic, bypassing RNG/pity/spin cost; validates the spell id exists via `sSpellMgr`.
- Config load validates `Chance.*` sums to 10000 (basis points) and that every rarity with nonzero chance has at least one valid `Rewards.<Rarity>` spell id — both log `LOG_ERROR` on mismatch, load proceeds (module still usable, but that rarity/roll will misbehave until fixed).
- Commands: `.mroulette spin <player>`, `.mroulette reward <player> <spellId>` (both require an online target — `learnSpell` needs a live `Player*`).
- New table `mod_mount_roulette_collection` (account_id, spell_id PK).
- New config keys in `mod_mount_roulette.conf.dist`: `Chance.<Rarity>`, `Rewards.<Rarity>`, `EpicPity`, `LegendaryPity`, `DuplicateShards.<Rarity>`, `ShardCost` (reserved, unused — see decisions.md open question #4).

**Files changed:**
- `modules/mod-mount-roulette/src/MountRouletteMgr.h`
- `modules/mod-mount-roulette/src/MountRouletteMgr.cpp`
- `modules/mod-mount-roulette/src/MountRouletteCommand.cpp`
- `modules/mod-mount-roulette/conf/mod_mount_roulette.conf.dist`
- `modules/mod-mount-roulette/data/sql/db-characters/b_mod_mount_roulette_collection.sql` (new)

**Verification:**
- build — PASS (`cmake --build . --target worldserver --config RelWithDebInfo`, exit 0, `worldserver.exe` relinked).
- runtime/gameplay (`EpicPity=3` series guarantees Epic on 3rd spin without Epic; duplicate → shards; 0 spins → refusal; <80 → refusal) — NOT VERIFIED.
- DB/log verification (pity/shards/collection rows match `MountRoulette.log`) — NOT VERIFIED.

**Known limitations / open items carried from the plan:**
- Default `Rewards.<Rarity>` config lists are empty — module needs real mount spell IDs filled in before spins can succeed in practice.
- Duplicate detection resolves open question #3 as **account-scoped** (checks `mod_mount_roulette_collection` by account_id, not per-character), matching the schema decision already recorded; not separately confirmed with the user.
- Shard spending mechanic (open question #4) still unresolved — shards only accumulate; `ShardCost` config key is reserved/unused.
- `ForceReward` awards duplicate shards at the Mythic tier regardless of the actual spell's rarity, since the GM picks the spell id directly and no rarity is rolled.

## Phase 4 — UI bridge (no AIO)

**Status:** Implemented, build PASS. Runtime/gameplay verification NOT VERIFIED (no real 3.3.5a client run this session; `worldserver.exe` could not be redeployed to `C:\azerothcore\server` — file locked, server appears to already be running; a restart/redeploy needs explicit permission).

Spike decision (see `decisions.md`): AIO confirmed technically compatible with `mod-ale`, but dropped anyway — no clean synchronous Lua→C++ call existed without ALE-core coupling, and AIO's only remaining value (auto-delivering the client addon) didn't justify pulling in third-party code. Used AzerothCore's built-in `AddonChannelCommandHandler` bridge instead (see `api.md`).

Implemented:
- `MountRouletteAddonBridge.cpp`: new `.roulette spin|info|collection` command table, `SEC_PLAYER`, self-target only, `Console::No`. Reuses `MountRouletteMgr::Spin`/`GetState` — no new business logic.
- Level gate enforced server-side for all three commands (`DenyIfBelowLevel`) — not just client-side hiding, per plan's "Отказ доступа для игроков <80 на сервере (не только скрытие UI)".
- `SendAddonPayload`: raw `CHAT_MSG_ADDON` (prefix `MTRLT`) reply with structured, pipe-delimited results, independent of the human-readable chat output.
- Client addon `client_addon/MountRoulette/` (`.toc` + `.lua`): window with SPIN/Collection buttons, spins/shards/pity display, `/mroulette` toggle. Talks to the server purely via the addon-command channel — no AIO, no new client dependency.
- Loader: `mmr_loader.cpp` registers the new command script.

**Files changed:**
- `modules/mod-mount-roulette/src/MountRouletteAddonBridge.cpp` (new)
- `modules/mod-mount-roulette/src/mmr_loader.cpp`
- `modules/mod-mount-roulette/client_addon/MountRoulette/MountRoulette.toc` (new)
- `modules/mod-mount-roulette/client_addon/MountRoulette/MountRoulette.lua` (new)

**Verification:**
- build — PASS (`cmake .` reconfigure + `cmake --build . --target worldserver --config RelWithDebInfo`, exit 0, `worldserver.exe` linked).
- runtime/gameplay (real 3.3.5a client: window opens, spin/info/collection round-trip, <80 denied server-side, forged client request can't bypass the level gate since it's enforced in the command handler, not the addon) — NOT VERIFIED.
- DB/log verification (spin still logs to `MountRoulette.log` and DB exactly as Phase 3 — this phase adds no new persistence path) — NOT VERIFIED this session (no worldserver run).

**Known limitations:**
- Client addon requires manual one-time install into `Interface/AddOns/` (no auto-delivery — traded away with AIO).
- `worldserver.exe` was not redeployed to the runtime server directory this session (target file locked/busy); the rebuilt binary sits in `build/bin/RelWithDebInfo/worldserver.exe` only.

## Phase 5 — World events framework + Invasion + World Boss

**Status:** Implemented, build PASS, runtime smoke-test PASS (worldserver started clean with the new module config, no crash, no missing-property errors for `WorldEvents.*`). Gameplay (actually running an invasion) NOT VERIFIED — `WaveEntry`/`EliteEntry`/`BossEntry` default to `0` (disabled), same as Phase 3's empty `Rewards.<Rarity>`; real creature entries must be filled in first.

Implemented:
- New module `modules/mod-world-events`. `WorldEventsMgr` (`WorldEventsMgr.h/.cpp`): single scripted event `"invasion"` — Idle → Waves (N waves) → Elite → Boss → Idle, each stage spawned via `Map::SummonCreature` at a configured point and tracked by `ObjectGuid` only.
- Stage advance: `Update(diff)` (from `WorldScript::OnUpdate`) checks only the tracked-summon list for the active stage (`IsStageCleared`) — no per-tick map scan; a per-stage timeout force-advances if never cleared.
- Optional random auto-start: config-gated accumulator (`RandomStart.Enable`, disabled by default) rolls a chance once per configured interval while idle.
- `.mevent start invasion` / `.mevent stop invasion` (GM); `Stop`/timeout/kill all route through the same `DespawnTracked()` (`TempSummon::UnSummon`).
- Cleanup on map unload via `AllMapScript::OnDestroyMap` (not `WorldMapScript` — invasion map id is config-driven, unknown at script-construction time).
- Boss kill credit via `PlayerScript::OnPlayerRewardKillRewarder`, filtered by configured boss entry and active Boss stage; routes through the existing `ServerActivitiesMgr::CreditActivity` with new activity ids `"worldevent"` / `"worldboss"` — no new table, no new manager in mod-server-activities.
- Config: `mod_world_events.conf.dist` (new file); `ServerActivities.WorldEvent.*` / `.WorldBoss.*` (Spins/DailyLimit) added to `mod_server_activities.conf.dist`.
- Loader: `we_loader.cpp` registers world/map/boss/command scripts.

**Files changed:**
- `modules/mod-world-events/src/WorldEventsMgr.h` (new)
- `modules/mod-world-events/src/WorldEventsMgr.cpp` (new)
- `modules/mod-world-events/src/WorldEventsWorldScript.cpp` (new)
- `modules/mod-world-events/src/WorldEventsMapScript.cpp` (new)
- `modules/mod-world-events/src/WorldEventsBossScript.cpp` (new)
- `modules/mod-world-events/src/WorldEventsCommand.cpp` (new)
- `modules/mod-world-events/src/we_loader.cpp` (new)
- `modules/mod-world-events/conf/mod_world_events.conf.dist` (new)
- `modules/mod-server-activities/conf/mod_server_activities.conf.dist` (added `WorldEvent.*`/`WorldBoss.*`)

**Verification:**
- build — PASS (`cmake .` reconfigure to discover the new module dir, then `cmake --build . --target worldserver --config RelWithDebInfo`, exit 0).
- runtime smoke test — PASS: worldserver started with the rebuilt binary and new `mod_world_events.conf` deployed to `C:\azerothcore\server\configs\modules\`; log shows `mod_world_events.conf` loaded, zero `Missing property WorldEvents.*` lines, `WORLD: World Initialized`, server reached the normal tick loop (playerbots running).
- gameplay (`.mevent start invasion` → waves → elite → boss → kill credit → `.mevent stop` cleanup) — NOT VERIFIED (needs real `WaveEntry`/`EliteEntry`/`BossEntry`/map coordinates filled in first; config ships with all three at `0`, which `StartEvent` refuses).
- DB/log verification (credit rows in `mod_server_activities_daily`, log lines) — NOT VERIFIED this session.

**Known limitations:**
- Invasion zone/creature entries/coordinates are unset by default (plan's open question #7 — "Детали World Events... не заданы" — still unresolved); a GM must configure `WorldEvents.Invasion.*` before the event can start.
- Only a single event id (`"invasion"`) exists; `.mevent start/stop` rejects any other id (Phase 7 scope).
- `ServerActivities.WorldEvent.*`/`WorldBoss.*` config keys have no `.Enable` flag (unlike other activities) — disabling is only possible via `DailyLimit = 0`.

## Phase 6 — Exploration, Profession, Fishing activities

**Status:** Implemented, build PASS. Runtime/gameplay and DB/log verification NOT VERIFIED (no worldserver run performed this session).

Hook feasibility check (plan's open question #6):
- `OnPlayerUpdateGatheringSkill`/`OnPlayerUpdateCraftingSkill` fire on **every** gather/craft attempt regardless of skill-up roll outcome or skill cap (confirmed by reading `Player::UpdateGatherSkill`/`UpdateCraftSkill` in `PlayerUpdates.cpp` — the hook call precedes the roll), but carry no item id, so they cannot identify *which* item was produced/gathered. Not used for crediting.
- `OnPlayerLootItem` (`Player::StoreLootItem`, `Player.cpp`) fires for any item actually taken from a lootable source — creature, gathering node, or fishing catch — and does carry the item. Used for both Profession and Fishing, gated by a configured item-id allowlist.
- `OnPlayerCanAreaExploreAndOutdoor` (`Player::CheckAreaExploreAndOutdoor`, `Player.cpp:5929`) fires on every position update inside any area, before core's own "already explored" bit check — so it cannot be used as-is without double-crediting. Implemented a read-only replica of core's own `PLAYER_EXPLORED_ZONES_1` bit check (same field/offset/bit math as `Player.cpp:5950-5955`) so credit only fires on a genuinely new area; the hook always returns `true` and never blocks core's own exploration/XP handling. No race: core sets the bit itself immediately after the hook returns, single-threaded.

Implemented:
- `ServerActivitiesExplorationScript` (`PlayerScript::OnPlayerCanAreaExploreAndOutdoor`): credits `exploration` once per day on true first-time area discovery (own bit check, described above).
- `ServerActivitiesLootScript` (`PlayerScript::OnPlayerLootItem`): credits `profession` and/or `fishing` when the looted item's entry is in the respective `ServerActivities.Profession.ItemIDs` / `ServerActivities.Fishing.ItemIDs` config list (comma-separated, `Acore::Tokenize` + `Acore::StringTo<uint32>`).
- Both route through the existing `ServerActivitiesMgr::CreditActivity` entry point — no new manager/scheduler added.
- Config: `ServerActivities.Exploration.*`, `ServerActivities.Profession.*` (incl. `ItemIDs`), `ServerActivities.Fishing.*` (incl. `ItemIDs`) added to `mod_server_activities.conf.dist`; `ItemIDs` empty by default (same empty-by-default posture as Phase 3's `Rewards.<Rarity>` and Phase 5's `WaveEntry`/etc — a GM must fill in real item ids before these two activities credit anything).
- Loader: `sa_loader.cpp` registers the two new scripts.

**Files changed:**
- `modules/mod-server-activities/src/ServerActivitiesExplorationScript.cpp` (new)
- `modules/mod-server-activities/src/ServerActivitiesLootScript.cpp` (new)
- `modules/mod-server-activities/src/sa_loader.cpp`
- `modules/mod-server-activities/conf/mod_server_activities.conf.dist`

**Verification:**
- build — PASS (`cmake .` reconfigure to discover the two new `.cpp` files, then `cmake --build . --target worldserver --config RelWithDebInfo`, exit 0, `worldserver.exe` relinked).
- runtime/gameplay (discover new area → +N spins once/day, re-enter same area → no credit; loot a configured Profession/Fishing item → credit; loot an unconfigured item → no credit; repeat same day → blocked by daily limit) — NOT VERIFIED.
- DB/log verification (`mod_server_activities_daily` rows for `exploration`/`profession`/`fishing`, `MountRoulette.log` lines) — NOT VERIFIED this session.

**Known limitations:**
- `Profession.ItemIDs`/`Fishing.ItemIDs` ship empty — no item qualifies until a GM configures real item entry IDs for rare crafts/gathers/fish.
- Fishing crediting is item-id based only; the plan's alternative "or a special zone" criterion (PRD/plan line: "рыбалки, зон ловли") was not implemented — no reliable way to tell "this looted item is a fish" from `ItemTemplate` alone (no dedicated fish subclass; would need a maintained item-class list), so zone-only fishing credit was left out rather than built on a shaky heuristic. Flagged, not resolved.
- Profession activity does not distinguish "rare" vs "common" beyond the configured id list — matches the plan's own item-id-list approach for Rewards/WaveEntry elsewhere in this feature.

## Phase 7.1 — World Random Events framework + City Defense (tracer bullet)

**Status:** Implemented, build PASS. Runtime/gameplay and DB/log verification NOT VERIFIED (no worldserver run this session; also blocked on missing `creature_template` rows — see Known limitations).

Implemented (generic framework, spec §2/§3/§21):
- `WorldEvent` (`WorldEvent.h/.cpp`): base class for any registry-driven event — lifecycle (`Inactive → Starting → Active → Success/Failed → Cleanup → Inactive`), participant registration/filtering, per-account daily-limit accounting, reward granting, and playerbot dispatch. A concrete event overrides `OnStart/OnUpdate/OnStop/OnCreatureKilled/OnSuccess/OnFailure/IsCompleted/IsFailed` only.
- `WorldEventRegistry` (`WorldEventRegistry.h/.cpp`): `string id -> factory` table. `CityDefenseEvent` self-registers via a static registrar object; adding a new event type is one more such file, no other code touched.
- `RewardMgr` (`RewardMgr.h/.cpp`): `RewardType::{Spin,Shards,Gold,Item}` abstraction so events never call `MountRouletteMgr` directly. `Spin` routes to `MountRouletteMgr::AddSpins`; `Gold`/`Item` use core `Player` APIs; `Shards` is a logged no-op (see decisions.md).
- `mod_world_events_daily` (account_id, event_id, day_key, count) — per-account daily-limit table for registry events, separate from `mod_server_activities_daily` (per-character, Phases 1-6).
- Playerbot dispatch (`WorldEvent::SendBotsToEvent`): selects up to `MaxParticipants` eligible bots (level gate, skips bots grouped with a human master per spec §9), balances Tank/Heal/DPS via `PlayerbotAI::IsTank/IsHeal`, sends same-map bots toward the event center via `MotionMaster::MovePoint` (see decisions.md for why not `TravelMgr`). Bots fight normally via their own `PlayerbotAI` once nearby; nothing forces their combat behavior. No persistent bot state is set, so there is nothing to leak — cleanup is a no-op by construction.
- `WorldEventsMgr` extended: `StartEvent`/`StopEvent`/`Update`/`OnMapDestroyed` branch on `eventId == "invasion"` (unchanged Phase 5 path) vs. everything else (registry-driven, `_active` unique_ptr). New: `OnPlayerCreatureKilled` (dispatches to the active event), `ListKnownEventIds`, `GetActiveEventId/State`, `ResetPlayerDaily`, `ForceCompleteEvent`, `GetPlayerDailyStatus`, debug flag, bot-dispatch readout.
- `WorldEventsParticipantScript.cpp` (new `PlayerScript::OnPlayerCreatureKill`): feeds player creature kills to the active generic event.
- GM commands (`WorldEventsCommand.cpp`, all `SEC_GAMEMASTER`): `.mevent start/stop/list/active/info/reset/complete/debug/bots`.

Implemented (City Defense, spec "EVENT 1"):
- `CityDefenseEvent` (`Events/CityDefenseEvent.h/.cpp`): Defense Captain spawned at event center; 4 waves of Invaders/Elite Invaders/Invasion Commander spawned at a random point 90-140 yards out (angle/distance random, height resolved via `Map::GetHeight`); next wave spawns once the previous wave's tracked summons are all dead (polled via `ObjectGuid` list, no map scans). Success = Commander killed while Captain alive; failure = Captain dies or a 15-minute (configurable) timeout elapses. Participant credit: any real/GM player (bots excluded in `WorldEvent::RegisterParticipant`) who kills an Invader/Elite/Commander while inside `CityDefense.Radius` of the center and `>= RequiredLevel`; final reward pass re-filters to participants still inside the radius when the Commander dies (skipped for `.mevent complete`, which is explicitly allowed to bypass objectives per spec §17). Reward defaults to 2 spins, daily limit 1/account.
- Config: `WorldEvents.MaxConcurrentEvents`, `WorldEvents.Playerbots.*`, `WorldEvents.CityDefense.*` added to `mod_world_events.conf.dist` (defaults match the spec's example: Goldshire coordinates, entries 910700-910703, 15-minute timeout, 2 spins).

**Files changed:**
- `modules/mod-world-events/src/WorldEvent.h` (new)
- `modules/mod-world-events/src/WorldEvent.cpp` (new)
- `modules/mod-world-events/src/WorldEventRegistry.h` (new)
- `modules/mod-world-events/src/WorldEventRegistry.cpp` (new)
- `modules/mod-world-events/src/RewardMgr.h` (new)
- `modules/mod-world-events/src/RewardMgr.cpp` (new)
- `modules/mod-world-events/src/Events/CityDefenseEvent.h` (new)
- `modules/mod-world-events/src/Events/CityDefenseEvent.cpp` (new)
- `modules/mod-world-events/src/WorldEventsParticipantScript.cpp` (new)
- `modules/mod-world-events/src/WorldEventsMgr.h`
- `modules/mod-world-events/src/WorldEventsMgr.cpp`
- `modules/mod-world-events/src/WorldEventsCommand.cpp`
- `modules/mod-world-events/src/we_loader.cpp`
- `modules/mod-world-events/conf/mod_world_events.conf.dist`
- `modules/mod-world-events/data/sql/db-characters/b_mod_world_events_daily.sql` (new)

**Verification:**
- build — PASS (`cmake .` reconfigure to discover new files, then `cmake --build . --target worldserver --config RelWithDebInfo`, exit 0, `worldserver.exe` relinked; one compile error found and fixed along the way — `sRandomPlayerbotMgr` is a reference, not a pointer, `.` not `->`).
- runtime/gameplay (`.mevent start citydefense` → waves → Commander death → reward; Captain death → failure; timeout → failure; <80 no reward; 80 reward; GM 80 reward; bots travel and fight; second same-day completion → no second reward; `.mevent reset` re-enables; `.mevent stop` cleans up; no orphan creatures/timers) — **NOT VERIFIED**, and currently **cannot** be verified as-is: entries 910700-910703 have no `creature_template` rows (see Known limitations), so `.mevent start citydefense` will spawn nothing until a GM adds them.
- DB/log verification (`mod_world_events_daily` rows, `MountRoulette.log` lines) — NOT VERIFIED this session.

**Known limitations:**
- **Blocking for actual gameplay**: `creature_template`/`creature_template_model` rows for 910700 (Defense Captain), 910701 (Invader), 910702 (Elite Invader), 910703 (Invasion Commander) do not exist yet. No SQL was written for them this session (see decisions.md) — a GM must add real templates (name, level, faction, display id, AI) before this event can run.
- `RewardType::Shards` and `RewardType::Item` (item id) paths are minimally exercised — no Phase 7.1 event uses them; only `Spin` (City Defense) and `Gold` have any real-world exercise path so far.
- Playerbot dispatch only moves bots already on the event's map; cross-continent bots are left to normal `PlayerbotAI` (see decisions.md) — on a fresh server where 3000 random bots are scattered across all continents, an unknown (unverified) fraction may actually be on Eastern Kingdoms/Goldshire's map at any given time.
- `.mevent bots` reports the *last* dispatch call's selected/travelling counts, not live bot position/state — matches spec's own description ("selected/travelling/arrived/dead...") only partially; "arrived"/"dead"/real-vs-GM breakdown were not implemented (would need per-bot state tracking not otherwise needed by City Defense).
- `WorldEvents.CityDefense.Reward.Type` other than `SPIN` will silently do nothing useful for `SHARDS` (logged, no payout) — acceptable since the shipped default and spec's own City Defense reward is `SPIN`.
- Updated `mod_world_events.conf.dist` was not redeployed to the runtime server config directory this session (no server restart/reload performed — requires explicit permission per project rules).

## Phase 7.2 — Caravan Escort, Random World Boss, Rare Hunt, Bounty Hunt

**Status:** Implemented, build PASS. Runtime/gameplay and DB/log verification NOT VERIFIED (no worldserver run this session; also blocked on missing `creature_template` rows for all 4 events' entries, same gap as Phase 7.1's City Defense).

No changes to the generic framework's shape were needed beyond one addition:
`WorldEvent::NotifyKillRewarded`/`OnKillRewarded`, fed from a new
`PLAYERHOOK_ON_REWARD_KILL_REWARDER` hook in `WorldEventsParticipantScript.cpp`
alongside the existing `OnPlayerCreatureKill` one — used only by Random World
Boss, which needs core's own multi-player/raid credit resolution rather than
"whoever landed the final hit". `.mevent list/start/stop/info/reset/complete/
bots` all work on the 4 new events with zero command-layer changes, since
they only ever call into `WorldEventRegistry`/`WorldEventsMgr` generically —
confirms the Phase 7.1 registry design pays for itself here.

Implemented:
- `CaravanEscortEvent` (`Events/CaravanEscortEvent.h/.cpp`): Supply Caravan
  spawns at Goldshire and is issued one `MotionMaster::MovePoint` to
  Westbrook Garrison; progress is polled each tick as
  `1 - (distance-to-destination / total-distance)`. Ambushes spawn once at
  25%/55% progress (`AmbushSize` raiders) and once at 80% (Raid Leader + 5,
  the spec's "Final" ambush). Success = caravan reaches within
  `ARRIVAL_DISTANCE` (10 yd) of the destination alive; failure = caravan
  dies or the 20-minute (configurable) timeout elapses. Credit: any
  real/GM player `>= RequiredLevel` who kills an Ambusher/Raider/Raid
  Leader (no radius check — combat naturally happens at the caravan).
- `RandomWorldBossEvent` (`Events/RandomWorldBossEvent.h/.cpp`): spawns one
  boss at Plaguewood (EPL) with configurable base health; every
  `RescaleIntervalSeconds` (default 15s) it recounts eligible participants
  (real/GM players and playerbots, level-gated, inside `Radius`) and
  rescales `MaxHealth`/`Health` to `BaseHealth * min(MaxHealthMultiplier,
  1 + (participants-1)*HealthPerExtraPlayerPct/100)`, preserving the
  current health *percentage* across a rescale rather than snapping it.
  Credit uses the new `OnKillRewarded` path (via `OnPlayerRewardKillRewarder`)
  so every player KillRewarder actually credits is registered, not just the
  finishing blow. Success = boss no longer alive; failure = 30-minute
  (configurable) timeout.
- `RareHuntEvent` (`Events/RareHuntEvent.h/.cpp`): one rare spawns at a
  random point from a configured list (`SpawnPoints`, `"x,y,z|x,y,z|..."`,
  parsed with `Acore::Tokenize`/`Acore::StringTo<float>`) in Duskwood.
  Success = killed; failure = 20-minute (configurable) timeout. Credit: the
  killer only (no group/raid credit — a solo/duo "hunt" per spec, no
  mention of shared tagging).
- `BountyHuntEvent` (`Events/BountyHuntEvent.h/.cpp`): all three fixed
  targets (A/B/C, distinct entries and coordinates) spawn together in
  Stranglethorn Vale at event start. Success = all three dead (tracked by
  a 3-element `_killedCount`/guid array, not a scan); failure = 20-minute
  (configurable) timeout. Credit: whoever lands each of the three kills
  (a player who kills 1 of 3 is still rewarded once the event as a whole
  succeeds — see decisions.md for why "progress per account" was read this
  way rather than as a per-account personal 3/3 requirement).
- Config: `WorldEvents.Caravan.*`, `WorldEvents.WorldBoss.*`,
  `WorldEvents.RareHunt.*`, `WorldEvents.BountyHunt.*` added to
  `mod_world_events.conf.dist`, defaults matching the spec's example data.

**Files changed:**
- `modules/mod-world-events/src/WorldEvent.h` / `.cpp` (added `OnKillRewarded`/`NotifyKillRewarded`)
- `modules/mod-world-events/src/WorldEventsMgr.h` / `.cpp` (added `OnPlayerKillRewarded` dispatch)
- `modules/mod-world-events/src/WorldEventsParticipantScript.cpp` (added `PLAYERHOOK_ON_REWARD_KILL_REWARDER`)
- `modules/mod-world-events/src/Events/CaravanEscortEvent.h` / `.cpp` (new)
- `modules/mod-world-events/src/Events/RandomWorldBossEvent.h` / `.cpp` (new)
- `modules/mod-world-events/src/Events/RareHuntEvent.h` / `.cpp` (new)
- `modules/mod-world-events/src/Events/BountyHuntEvent.h` / `.cpp` (new)
- `modules/mod-world-events/conf/mod_world_events.conf.dist`

**Verification:**
- build — PASS (`cmake .` reconfigure to discover the 4 new event files, then
  `cmake --build . --target worldserver --config RelWithDebInfo`, exit 0,
  `worldserver.exe` relinked; one compile error found+fixed —
  `Acore::StringTo` needs `StringConvert.h`, `Tokenize.h` alone doesn't pull it in).
- runtime/gameplay (all four events: start → objective → success; start →
  timeout/death → failure; <80 no reward; daily limit; `.mevent reset`;
  `.mevent stop` cleanup; world boss health actually rescales with
  participant count) — **NOT VERIFIED**, and currently **cannot** be
  verified as-is: none of entries 910710-910713, 910720, 910730,
  910740-910742 have `creature_template` rows.
- DB/log verification — NOT VERIFIED this session.

**Known limitations:**
- **Blocking for actual gameplay**: no `creature_template`/`creature_template_model`
  rows exist for any of the 4 events' 9 new creature entries — same gap as
  Phase 7.1, not resolved here for the same reason (no DB access this
  session to verify a chosen display id, see decisions.md).
- Random World Boss's participant scaling counts playerbots via
  `RandomPlayerbotMgr::GetAllBots()` filtered by map/radius/level each
  rescale tick — not cached, but bounded by however many bots exist
  server-wide (a fixed, known cost, not proportional to world size); not
  measured against a live 3000-bot instance this session.
- Bounty Hunt's "progress per account" reading (reward anyone who landed
  >=1 of the 3 kills, not a personal 3/3 requirement) is a judgment call —
  flagged in decisions.md, not confirmed with the user.
- Caravan's ambush spawn points are relative to the caravan's *current*
  position when a threshold is crossed (not fixed waypoints) — reasonable
  given the caravan follows a pathfound route whose midpoint isn't known in
  advance, but means ambush location varies run to run.

## Phase 7.3 — Portal Event, Treasure Hunt, Resource Rush

**Status:** Implemented, build PASS (first try, no compile errors). Runtime/gameplay and DB/log verification NOT VERIFIED (no worldserver run this session; also blocked on missing `creature_template`/`gameobject_template`/`item_template` rows, same gap as 7.1/7.2).

Two of these three events are structurally different from every prior Phase 7 event: Treasure Hunt and Resource Rush reward per player action while the event runs (open a chest, hand in gathered fragments), not once at a shared pass/fail resolution. Rather than force them into the `OnSuccess()`-grants-everyone shape, the framework gained:
- `WorldEvent::OnItemLooted`/`NotifyItemLooted`, fed from a new `PLAYERHOOK_ON_LOOT_ITEM` hook in `WorldEventsParticipantScript.cpp` — `lootSourceGuid` identifies the creature/gameobject looted, matched against an event's own tracked guids.
- `WorldEvent::TryRewardPlayer(player, type, amount, dailyLimit, requiredLevel)` — the same level+daily-limit+grant logic `GrantRewardsToParticipants` already had, factored out so it can be called once per qualifying action instead of only in a batch at `OnSuccess()`. `GrantRewardsToParticipants` now calls it internally; no behavior change for Phase 7.1/7.2 events.

Implemented:
- `PortalEventEvent` (`Events/PortalEventEvent.h/.cpp`): decorative Unstable Portal marker (a gameobject; a missing/invalid entry doesn't block anything else) plus 3 waves (10 mobs -> 12 mobs+2 elites -> Portal Boss+6 mobs) at Lakeshire, same tracked-summon wave-clear pattern as City Defense/Caravan. Success = Portal Boss killed; failure = 20-minute (configurable) timeout only (no NPC-to-protect objective).
- `TreasureHuntEvent` (`Events/TreasureHuntEvent.h/.cpp`): spawns one chest gameobject per configured point (5 by default, matching the spec's 5 Stranglethorn coordinates for `ChestCount = 5`). `OnItemLooted` matches the loot source guid against the tracked chest list; the opening player is rewarded immediately via `TryRewardPlayer`. Event "succeeds" (for cleanup/announce purposes) once every chest is opened, or ends on a 20-minute (configurable) timeout with unopened chests deleted.
- `ResourceRushEvent` (`Events/ResourceRushEvent.h/.cpp`): spawns `NodeCount` (30 default) Meteor Fragment Node gameobjects scattered randomly within `Radius` of Thorium Point. Looting a node is ordinary gameobject loot (an `item_template`/`gameobject_loot_template` data gap, see Known limitations) — `OnItemLooted` then checks `Player::GetItemCount(FragmentItemId) >= RequiredFragments`; if so, `DestroyItemCount` consumes 10 and the player is rewarded via `TryRewardPlayer`. Node respawn (spec: 60s) is **core's own GameObject respawn timer** (`Map::SummonGameObject`'s `respawnTime` param), not custom code — see decisions.md. This event has no shared "success": `IsCompleted()` is always `false`; it just runs for `DurationMinutes` (default 20) and then ends (nodes deleted), which `OnFailure()` announces neutrally rather than as a loss.
- Config: `WorldEvents.PortalEvent.*`, `WorldEvents.TreasureHunt.*`, `WorldEvents.ResourceRush.*` added to `mod_world_events.conf.dist`, defaults matching the spec's example data.

**Files changed:**
- `modules/mod-world-events/src/WorldEvent.h` / `.cpp` (added `OnItemLooted`/`NotifyItemLooted`, `TryRewardPlayer`; `GrantRewardsToParticipants` refactored to use it)
- `modules/mod-world-events/src/WorldEventsMgr.h` / `.cpp` (added `OnPlayerItemLooted` dispatch)
- `modules/mod-world-events/src/WorldEventsParticipantScript.cpp` (added `PLAYERHOOK_ON_LOOT_ITEM`)
- `modules/mod-world-events/src/Events/PortalEventEvent.h` / `.cpp` (new)
- `modules/mod-world-events/src/Events/TreasureHuntEvent.h` / `.cpp` (new)
- `modules/mod-world-events/src/Events/ResourceRushEvent.h` / `.cpp` (new)
- `modules/mod-world-events/conf/mod_world_events.conf.dist`

**Verification:**
- build — PASS (`cmake .` reconfigure to discover the 3 new event files, then
  `cmake --build . --target worldserver --config RelWithDebInfo`, exit 0,
  `worldserver.exe` relinked; no compile errors this round).
- runtime/gameplay (Portal: waves → boss → reward; Treasure Hunt: open a
  chest → immediate reward, daily limit on a 2nd chest same day, all 5
  opened → event ends; Resource Rush: loot 10 fragments → consumed +
  rewarded, node respawns after 60s; `.mevent stop` cleanup for all three)
  — **NOT VERIFIED**, and currently **cannot** be verified as-is: none of
  910750-910753 (creatures/GO), 910760 (chest GO), 910770/920770
  (node GO / fragment item) exist in the world database.
- DB/log verification — NOT VERIFIED this session.

**Known limitations:**
- **Blocking for actual gameplay**: same data gap as every prior Phase 7
  sub-phase — no `creature_template`, `gameobject_template`,
  `gameobject_loot_template`, or `item_template` rows for this phase's 6 new
  entries. Treasure Hunt and Resource Rush additionally need a
  `gameobject_loot_template` row on their chest/node so looting is possible
  at all (core's loot UI has nothing to open otherwise) — not created this
  session, same reasoning as before (no DB access to verify against this
  install).
- Resource Rush's node respawn relies on core's own GameObject
  respawn-after-loot behavior for a `Map::SummonGameObject`-spawned (not
  DB-spawned) object; this session verified the *code path* (compiles,
  calls the documented API) but not the actual respawn behavior at runtime
  (no worldserver run, no gameobject_loot_template to make the node
  lootable in the first place).
- Treasure Hunt/Resource Rush rewards bypass `RegisterParticipant`/
  `GrantRewardsToParticipants` entirely (they call `TryRewardPlayer`
  directly per action) — `.mevent complete <player> treasure` would call
  the generic `ForceComplete` → `OnSuccess()` path, which for
  `TreasureHuntEvent` only announces and does not itself grant a reward
  (already-opened chests were rewarded at open time). This is intentional
  given the event's shape, but differs from City Defense/Caravan/etc.,
  where `.mevent complete` does grant a reward — flagged so a GM isn't
  surprised.

## Phase 7.4 — Server Wide Event, Corrupted Zone, Dungeon Event, Fishing Frenzy, World PvP Event

**Status:** Implemented, build PASS (first try, no compile errors). Runtime/gameplay and DB/log verification NOT VERIFIED (no worldserver run this session). This closes out Phase 7 (all 13 World Random Events from the spec are now implemented).

The framework gained 5 more dispatch points to cover mechanics no earlier
event needed:
- `OnCreatureSpawned`/`NotifyCreatureSpawned`, fed from a new
  `AllCreatureScript::OnCreatureAddWorld` hook (`WorldEventsZoneModifierScript.cpp`)
  — per-spawn, not a per-tick zone scan. Used by Corrupted Zone (filters by
  zone id) and Dungeon Event (filters by map id) to apply a one-time
  health/damage buff to qualifying hostile creatures.
- `OnDungeonCompleted`/`NotifyDungeonCompleted`, fed from a new
  `GlobalScript::OnAfterUpdateEncounterState` hook (`WorldEventsDungeonScript.cpp`,
  mirrors mod-server-activities' own dungeon hook but is a fully separate,
  independent credit path). Used by Dungeon Event.
- `OnFishingAttempt`/`NotifyFishingAttempt`, fed from
  `PLAYERHOOK_ON_UPDATE_FISHING_SKILL` (added to `WorldEventsParticipantScript.cpp`).
  Used by Fishing Frenzy to roll its own independent bonus-catch chance.
- `OnPvpKill`/`NotifyPvpKill`, fed from `PLAYERHOOK_ON_PVP_KILL` (same
  file). Used by World PvP Event.
- `OnGossipAction`/`NotifyGossipAction`, fed from a new gossip
  `CreatureScript` (`WorldEventsQuartermasterScript.cpp`). Used by Server
  Wide Event.

All 5 new events share one structural trait: none has a shared pass/fail
resolution (`IsCompleted()` is always `false` for 4 of them; Server Wide
Event's is server-goal-driven but personal rewards are still per-action).
Every reward in this sub-phase goes through `TryRewardPlayer` (Phase 7.3's
addition), not `GrantRewardsToParticipants`.

Implemented:
- `ServerWideEventEvent` (`Events/ServerWideEventEvent.h/.cpp`): a
  persistent, GM-placed War Effort Quartermaster NPC (not summoned by this
  module) accepts donations of configured items via a 4-option gossip menu
  (Donate 1/10/20/All). Each donation is actually removed from the player's
  inventory (`DestroyItemCount`) and counted toward both a personal total
  (in-memory, per account) and the shared server total. Crossing
  `PersonalGoal` (50) rewards immediately; the server reaching `ServerGoal`
  (1000) just ends the event with an announcement — spec gives no separate
  reward for the server goal itself.
- `CorruptedZoneEvent` (`Events/CorruptedZoneEvent.h/.cpp`): while active,
  every hostile, non-critter, non-pet creature `>= MinCreatureLevel`
  spawning in `ZoneId` gets `HealthMultiplier`/`DamageMultiplier` applied
  once via `Unit::SetMaxHealth`/`Unit::ApplyStatPctModifier` (the latter on
  `UNIT_MOD_DAMAGE_MAINHAND/OFFHAND/RANGED`, `TOTAL_PCT`). Personal kill
  objective (`RequiredKills`, tracked per account in-memory) rewards
  immediately on completion.
- `DungeonEventEvent` (`Events/DungeonEventEvent.h/.cpp`): same
  spawn-buff mechanism as Corrupted Zone, filtered by a configurable pool
  of dungeon map ids (default: Utgarde Pinnacle 575, Halls of Lightning
  602, The Oculus 578, Culling of Stratholme 595, Gundrak 604 — taken from
  this repo's own `mod-dungeon-clear/.../DungeonEventTables.h`, not
  guessed). Every player on the map when its final boss dies is rewarded
  immediately, gated by `AllowActivityRewardStacking` (default on).
- `FishingFrenzyEvent` (`Events/FishingFrenzyEvent.h/.cpp`): every fishing
  attempt in `ZoneId` independently rolls `EventFishChancePct` for one bonus
  Frenzy Fish item, additive to the normal catch (never blocks or replaces
  it — the hook always returns `true`). Hand-in at `RequiredFish` rewards
  immediately.
- `WorldPvpEventEvent` (`Events/WorldPvpEventEvent.h/.cpp`): a PvP kill
  inside the Gurubashi Arena radius counts toward the killer's
  `RequiredUniqueKills` only if: killer != killed, both inside the radius,
  the victim isn't a bot, killer/killed aren't the same account, at least
  `MinRealParticipants` real players are currently in the radius, and this
  particular victim hasn't already been credited once this event (global
  `std::set<ObjectGuid>`, not per-killer — spec's "same victim only once
  per event" read as event-wide). Rewards immediately on threshold.
- Config: `WorldEvents.ServerWide.*`, `WorldEvents.CorruptedZone.*`,
  `WorldEvents.DungeonEvent.*`, `WorldEvents.FishingFrenzy.*`,
  `WorldEvents.WorldPvP.*` added to `mod_world_events.conf.dist`.

**Files changed:**
- `modules/mod-world-events/src/WorldEvent.h` / `.cpp` (added `OnCreatureSpawned`/`OnDungeonCompleted`/`OnFishingAttempt`/`OnPvpKill`/`OnGossipAction` + `Notify*` dispatchers)
- `modules/mod-world-events/src/WorldEventsMgr.h` / `.cpp` (added matching dispatch methods)
- `modules/mod-world-events/src/WorldEventsParticipantScript.cpp` (added `PLAYERHOOK_ON_UPDATE_FISHING_SKILL`, `PLAYERHOOK_ON_PVP_KILL`)
- `modules/mod-world-events/src/WorldEventsZoneModifierScript.cpp` (new — `AllCreatureScript::OnCreatureAddWorld`)
- `modules/mod-world-events/src/WorldEventsDungeonScript.cpp` (new — `GlobalScript::OnAfterUpdateEncounterState`)
- `modules/mod-world-events/src/WorldEventsQuartermasterScript.cpp` (new — gossip `CreatureScript`)
- `modules/mod-world-events/src/Events/ServerWideEventEvent.h` / `.cpp` (new)
- `modules/mod-world-events/src/Events/CorruptedZoneEvent.h` / `.cpp` (new)
- `modules/mod-world-events/src/Events/DungeonEventEvent.h` / `.cpp` (new)
- `modules/mod-world-events/src/Events/FishingFrenzyEvent.h` / `.cpp` (new)
- `modules/mod-world-events/src/Events/WorldPvpEventEvent.h` / `.cpp` (new)
- `modules/mod-world-events/src/we_loader.cpp`
- `modules/mod-world-events/conf/mod_world_events.conf.dist`

**Verification:**
- build — PASS (`cmake .` reconfigure to discover the new script/event
  files, then `cmake --build . --target worldserver --config RelWithDebInfo`,
  exit 0, `worldserver.exe` relinked; no compile errors this round).
- runtime/gameplay — **NOT VERIFIED**, and currently **cannot** be verified
  as-is for the same recurring reason: no `creature_template`/
  `gameobject_template`/`item_template` rows for entry 910780 (Quartermaster)
  or item 920790 (Frenzy Fish); `CorruptedZone.ZoneId` and
  `FishingFrenzy.ZoneId` also ship as `0` (disabled) because this session
  had no way to confirm Icecrown's/Grizzly Hills' exact zone id against
  this install (see Known limitations — these are the first two Phase 7
  config values left at a disabling default specifically for that reason,
  as opposed to missing creature/item data).
- DB/log verification — NOT VERIFIED this session.

**Known limitations:**
- **Blocking for actual gameplay**: `creature_template.ScriptName` for
  entry 910780 must be set to `npc_war_effort_quartermaster` (this session
  wrote the script but not the DB row); item 920790 needs an
  `item_template` row; `CorruptedZone.ZoneId`/`FishingFrenzy.ZoneId` need
  real zone ids filled in (defaulted to `0`/disabled rather than guessed —
  unlike map ids, which this session could and did verify against this
  repo's own `mod-dungeon-clear` data).
- `DungeonEventEvent`'s health/damage buff and completion credit are two
  independent mechanisms (`OnCreatureSpawned` buffs mobs already in the
  dungeon map pool; `OnDungeonCompleted` credits players in the instance
  when its `dungeonCompleted` flag flips) — both were exercised only at
  compile time, not verified together in an actual dungeon run.
- Server Wide Event's personal/server point totals are in-memory only
  (`std::unordered_map`/`uint32` inside the event instance) — a worldserver
  restart mid-event loses all standing donations, same class of limitation
  already accepted for other in-memory per-event state (bot dispatch info,
  etc.) rather than adding new persistence for a short-lived daily event.
- Corrupted Zone's buff only applies to creatures that spawn *after* the
  event starts (`OnCreatureAddWorld` fires on spawn/respawn) — already-alive
  creatures in the zone when the event starts are not retroactively
  buffed. Accepted rather than adding a startup zone scan, which the
  project's own performance rules discourage ("avoid ... global scans every
  tick" — a one-time scan at start is cheaper but still an unrequested
  scope addition not asked for by the spec).
- World PvP Event's "same victim only once per event" is implemented as a
  single global set shared by all killers (first kill of a given victim is
  the only one that ever counts, for anyone) — a judgment call on an
  ambiguous spec line, flagged in decisions.md.

## Phase 7 summary

All 13 events from the original spec are implemented: City Defense (7.1),
Caravan Escort / Random World Boss / Rare Hunt / Bounty Hunt (7.2), Portal
Event / Treasure Hunt / Resource Rush (7.3), Server Wide Event / Corrupted
Zone / Dungeon Event / Fishing Frenzy / World PvP Event (7.4). Every phase
built PASS. The generic `WorldEvent`/`WorldEventsMgr`/`WorldEventRegistry`
framework built in 7.1 absorbed all 12 further events without ever
touching GM commands, the scheduler, or playerbot dispatch — only growing
by adding new `On*`/`Notify*` hook pairs when a genuinely new mechanic
(loot, gossip, zone spawn, dungeon completion, fishing, PvP) appeared that
no earlier event's hooks covered.

## Phase 7 — runtime verification (post-implementation session)

**Status:** All 13 events runtime-verified via SOAP GM commands against a
live worldserver. `.mevent start <id>` → `.mevent active` (state 2 =
Active) → `.mevent stop` was exercised for every event id: `citydefense`,
`caravan`, `worldboss`, `rarehunt`, `bounty`, `portal`, `treasure`,
`resourcerush`, `serverwide`, `dungeonevent`, `corruptedzone`, `fishing`.
This confirms scheduling/lifecycle/cleanup only — it does not replace
gameplay verification (actual combat, loot rolls, reward payout, bot
dispatch behavior in a live client), which remains not done.

Data gaps from 7.1-7.4's Known limitations closed this session:
- `creature_template`/`creature_template_model` rows for all 17 Phase 7
  creature entries (910700-910703, 910710-910713, 910720, 910730,
  910740-910742, 910751-910753, 910780) — drafted from verified real rows
  in this repo's own `data/sql/base/db_world/*.sql`, imported into
  `acore_world`.
- `gameobject_template`/`gameobject_loot_template` rows for the 3 Phase 7
  gameobject entries (910750 Unstable Portal, 910760 Event Treasure Chest,
  910770 Meteor Fragment Node) — imported.
- `item_template`/`item_dbc` rows for 920770 (Meteor Fragment) and 920790
  (Frenzy Fish), cloned from real items 2589/6291 — imported.
- `WorldEvents.CorruptedZone.ZoneId` = **210** (Icecrown),
  `WorldEvents.FishingFrenzy.ZoneId` = **394** (Grizzly Hills) — verified
  against this repo's own `data/sql/base/db_world/graveyard_zone.sql`
  (entries named `"... - Icecrown"` / `"... - Grizzly Hills"` use those
  ids), no longer left at the disabling default of `0`.

Real bug found and fixed by this verification pass:
- `WorldEvent::Start()` (`WorldEvent.cpp`) unconditionally forced
  `SetState(Active)` after calling `OnStart()`, silently overwriting a
  `Failed` state an event's `OnStart` had just set (e.g. Corrupted
  Zone/Fishing Frenzy refusing to start with `ZoneId = 0`). Effect: a
  misconfigured event reported "started" and actually ran instead of
  refusing. Fix: only advance to `Active` if `OnStart` did not already set
  `Failed`. Verified before/after: pre-fix, `.mevent start corruptedzone`
  with `ZoneId = 0` returned `"corruptedzone started."` and
  `.mevent active` showed state 2 (Active); post-fix, the same command
  returns `"Event failed to start"` and `.mevent active` shows no active
  event.

Unrelated pre-existing issue found and fixed in passing (not caused by
Phase 7): the live `configs/modules/mod_server_activities.conf` was stale
(10 of 33 documented keys present), missing the `Exploration`/
`Profession`/`Dungeon`/`Raid`/`Loot`/`Achievement` config blocks entirely.
Every present key matched its compiled-in default, so behavior was
unaffected, but `ServerActivitiesExplorationScript`'s
`OnPlayerCanAreaExploreAndOutdoor` hook (fires on every player position
update) logged an uncached "Missing property" warning on every call,
flooding `Server.log` under playerbot load. Fixed by redeploying the full
`mod_server_activities.conf.dist` (values unchanged) and `.reload config`.

Still not verified: actual gameplay (combat outcomes, loot rolls, reward
payout amounts, playerbot dispatch/combat behavior, DB row correctness for
`mod_world_events_daily`) — this pass only confirms each event's
start/active/stop lifecycle responds correctly via SOAP, including the two
previously-blocked "should refuse" cases.
