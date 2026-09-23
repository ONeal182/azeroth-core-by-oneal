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
- **Duplicate detection is account-scoped** (open question #3): "already
  learned" is checked against `mod_mount_roulette_collection` by
  `account_id`, not per-character. Follows directly from the collection
  table being account-scoped in the original schema decision; a learned
  mount is not re-taught to other characters on the same account, it just
  stops being a "new" result for future spins on that account. Not
  separately confirmed with the user — flagged, not resolved.
- **Shard spending (open question #4) stays unresolved this phase**: shards
  only accumulate via `DuplicateShards.<Rarity>`. `MountRoulette.ShardCost`
  config key exists (per PRD) but nothing reads it yet — no spend/exchange
  mechanic was added.
- **Rarity RNG is a single cumulative roll** (`urand(1,10000)` against
  `Chance.*` basis points in enum order Common→Mythic), not per-rarity
  independent rolls, so the configured percentages are exact rather than
  approximate. Pity overrides the roll entirely rather than reweighting it:
  Legendary pity is checked before Epic pity, matching the plan's stated
  priority.
- **`ForceReward` (`.mroulette reward`) treats the GM-picked spell as
  Mythic tier for duplicate-shard payout**, since no rarity is rolled for a
  forced reward and the manager has no per-spell rarity lookup table.
- **Phase 4 bridge: AzerothCore's built-in addon-command channel, not AIO**
  (open question #1/#2, spike outcome). Investigated whether AIO (Rochet2/AIO)
  runs on `mod-ale`: numerically confirmed compatible (`RegisterServerEvent(30,
  ...)`/`RegisterPlayerEvent(4/42, ...)` match ALE's `ServerEvents`/`PlayerEvents`
  enum exactly, despite ALE's README claiming general Eluna-script
  incompatibility). Rejected anyway: AIO would only have bought auto-delivery
  of the client addon file, while every actual RPC call still had no clean
  path from AIO's Lua layer into `MountRouletteMgr` (ALE exposes no public
  C++ hook for third-party modules to register Lua globals; the only
  synchronous options were `RunCommand` — async/CLI-only, no return value —
  or touching ALE internals directly, which is a core-adjacent coupling this
  module shouldn't take for a UI feature). Chatting through
  `AddonChannelCommandHandler` (`src/server/game/Chat/Chat.cpp:1063`) gets a
  synchronous, permission-checked call into the exact same command table used
  by typed commands, with zero AIO/third-party code and zero ALE coupling.
  Traded away: automatic addon delivery — the client addon
  (`client_addon/MountRoulette/`) needs a one-time manual copy into
  `Interface/AddOns/` per player, same as any manually-distributed addon.
- **Phase 5 invasion cleanup uses `AllMapScript::OnDestroyMap`, not
  `WorldMapScript`**: `WorldMapScript`'s constructor takes a fixed `mapId` at
  script-construction time, but `WorldEvents.Invasion.MapId` is only known
  after config loads (which happens via a later hook, same ordering issue
  `ServerActivitiesWorldScript`/`MountRouletteWorldScript` already rely on).
  `AllMapScript` fires for every map and the handler filters on
  `map->GetId() == sWorldEventsMgr->GetInvasionMapId()` itself.
- **Single hardcoded event id, `"invasion"`**: `StartEvent`/`StopEvent` take a
  `std::string eventId` for the `.mevent start|stop <id>` command shape the
  plan specifies, but only `"invasion"` is implemented — no event registry/table,
  per the plan's Phase 5 scope (Phase 7 is where multiple event types are added).
- **Stage advance is driven by a tracked `ObjectGuid` list, not a scan**:
  `IsStageCleared()` only calls `Map::GetCreature(guid)` on the (≤ few) guids
  captured at spawn time, matching the plan's "без сканов каждый тик"
  constraint. A per-stage timeout (`*.TimeoutSeconds`) force-advances if the
  stage is never cleared, so a stuck/unreachable spawn can't wedge the event
  forever; `.mevent stop` is also always available.
- **Random auto-start is a config-gated accumulator** (`RandomStart.Enable`,
  disabled by default), not a live default: `WorldEventsMgr::Update` rolls
  `urand(1,100)` against `RandomStart.ChancePercent` once per
  `RandomStart.IntervalSeconds` while idle. Satisfies the plan's "запуск по
  таймеру ... с накопителем" task without a generic scheduler abstraction.
- **`WorldEvents.Invasion.WaveEntry`/`EliteEntry`/`BossEntry` default to `0`
  (disabled)** — PRD/plan open question #7 (exact zone/NPC/reward details)
  is unresolved, so `StartEvent` refuses with a message instead of spawning
  entry `0`. Same empty-by-default posture as Phase 3's `Rewards.<Rarity>`.
- **Phase 6 exploration credit replicates core's own explored-area bit check
  instead of trusting `OnPlayerCanAreaExploreAndOutdoor` alone**: that hook
  fires on every position update within any area (it gates core's per-tick
  explore/outdoor recalculation, not just first discovery), so crediting on
  every call would double/triple-credit while a player idles in an already-
  explored zone. The script reads the same `PLAYER_EXPLORED_ZONES_1` field/
  offset/bit math core uses right after the hook returns (`Player.cpp:5950-
  5955`) and only credits when the bit isn't set yet; it never writes the
  bit itself, so there's no divergence from core's own bookkeeping.
- **Phase 6 profession/fishing use `OnPlayerLootItem`, not the skill-update
  hooks**: `OnPlayerUpdateGatheringSkill`/`OnPlayerUpdateCraftingSkill` fire
  on every gather/craft attempt (confirmed unconditional in
  `Player::UpdateGatherSkill`/`UpdateCraftSkill`, independent of skill cap or
  roll outcome — this resolves the plan's open question #6 about hooks not
  firing at max skill: they do fire, cap or not), but neither carries an item
  id, so a "rare item" allowlist can't be applied there. `OnPlayerLootItem`
  fires once an item is actually taken from any lootable source (creature,
  node, fishing catch) and does carry the item, so both activities key off
  it with a configured `ItemIDs` allowlist instead.
- **Fishing's "or a special zone" criterion (plan/PRD) was dropped for Phase
  6, not implemented as a heuristic**: there is no dedicated "this is a fish"
  item flag in `ItemTemplate` (checked `ItemTemplate.h` — no fish subclass
  exists, only crafting-recipe/tool subclasses), so a zone-only "any catch
  counts" rule would have needed a maintained fish-item-class guess. Left
  unresolved rather than building on that guess; `Fishing.ItemIDs` (exact
  item list) is the only supported mechanism this phase.
- **Structured results ride a second, app-defined addon-message prefix
  (`MTRLT`)**, separate from `AddonChannelCommandHandler`'s own `"AzerothCore\t"`
  ack/output protocol, so the client UI parses simple pipe-delimited fields
  instead of scraping human-readable chat text. Sent with the same
  `WorldPacket`/`ChatHandler::BuildChatPacket` pattern `mod-ale`'s
  `player:SendAddonMessage` uses (`CHAT_MSG_WHISPER`, `LANG_ADDON`,
  self-to-self), no new wire mechanism invented.
- **Phase 7.1 adds a generic `WorldEvent` base class + `WorldEventRegistry`
  additively, next to the untouched Phase 5 invasion code**, instead of
  refactoring Invasion into the new framework. Reasoning: the caller's spec
  for Phase 7 asks for a registry so adding e.g. `DragonInvasionEvent` never
  touches `WorldEventsMgr`/scheduler/commands/playerbot dispatch again; but
  rewriting the already-working, already-documented Invasion event carried
  regression risk for no requested benefit (spec's own DoD list is entirely
  about City Defense). `WorldEventsMgr::StartEvent/StopEvent/Update/
  OnMapDestroyed` now branch: `eventId == "invasion"` keeps the exact Phase 5
  path; anything else goes through `WorldEventRegistry`. Revisit only if a
  concrete reason to unify appears (e.g. invasion needs a feature the
  registry provides, like reward-per-account daily limits).
- **Playerbot dispatch uses `Player::GetMotionMaster()->MovePoint(...)`
  (core's point-movement generator), not mod-playerbots' `TravelMgr`/
  `TravelTarget`**: `TravelTarget` (`modules/mod-playerbots/src/Mgr/Travel/
  TravelMgr.h`) is owned by `PlayerbotAI`'s own action state machine
  (prepare/travel/work/cooldown, retry counters, a "forced" flag consumed
  elsewhere in that engine); setting one from outside without also driving
  that state machine correctly risks fighting the bot's own AI rather than
  guiding it. `MovePoint` is the same core movement generator creatures and
  other bot actions already use — not a hand-rolled pathfinder, not a
  teleport (spec §8's actual constraints) — so it satisfies the letter of
  the requirement even though it isn't literally `TravelMgr`. Cross-map bots
  are left alone entirely (no forced recall) rather than teleported, per the
  same constraint. Documented as a deviation, not silently substituted.
- **Bot role balance reuses `PlayerbotAI::IsTank/IsHeal(Player*)` static
  predicates** (already used project-wide for role checks) for City
  Defense's round-robin bot selection — no new role/spec classification was
  added.
- **World event daily limits are account-scoped in their own table**
  (`mod_world_events_daily`), separate from `mod_server_activities_daily`:
  the spec requires per-account limits for events, but the existing
  `ServerActivitiesMgr::CreditActivity` table is keyed by character `guid`
  (per-character, matching Phases 1-6's own activities). Reusing that table
  with an account id in the `guid` column would silently change its meaning
  for every other activity; a second small table with the same shape
  (`account_id`, `event_id`, `day_key`, `count`) keeps both mechanisms
  correct without touching `mod-server-activities`.
- **City Defense creature entries (910700-910703) are reserved in config
  but no `creature_template` SQL was written this phase**: same posture as
  Phase 3's empty `Rewards.<Rarity>` and Phase 5's `WaveEntry=0` — a GM must
  add real `creature_template`/`creature_template_model` rows for these
  entries (Defense Captain / Invader / Elite Invader / Invasion Commander)
  before `.mevent start citydefense` can spawn anything. Not guessed at
  because this session has no DB access to verify a chosen model/display id
  is valid on this install, and writing plausible-looking but unverified
  creature data would be worse than an explicit gap.
- **`RewardType::Shards` has no backing implementation**: `MountRouletteMgr`
  exposes no public shard mutator outside the spin/duplicate-reward path
  (see Phase 3 decisions above), and no Phase 7.1 event needs it (City
  Defense defaults to `SPIN`). `RewardMgr::RewardPlayer` logs an error and
  grants nothing for `Shards` rather than adding a new mutator speculatively
  ahead of an event that actually needs it.
- **Phase 7.2 adds `WorldEvent::OnKillRewarded`/`NotifyKillRewarded`, fed
  from a second hook (`PLAYERHOOK_ON_REWARD_KILL_REWARDER`) alongside the
  Phase 7.1 `OnCreatureKilled`/`PLAYERHOOK_ON_CREATURE_KILL` path**, rather
  than switching every event to one or the other. `OnPlayerCreatureKill`
  only fires for the player who lands the killing blow — fine for City
  Defense/Caravan/Rare Hunt/Bounty Hunt, which don't need raid-wide credit.
  Random World Boss does: it's designed for a group/raid to scale against,
  and core's `KillRewarder` (used identically by Phase 2's raid-boss
  activity and Phase 5's invasion boss) already resolves who in the
  group/raid/proximity gets credit. Reusing that resolution is one hook
  add, not a parallel credit-tracking system.
- **Random World Boss rescales health periodically (every
  `RescaleIntervalSeconds`), not once at spawn**: the spec's own health
  formula is a function of "participants... actually located in the event
  radius", which changes as players arrive/leave/die over a fight that can
  run many minutes. A fixed-at-spawn scale would either punish an empty
  pull or fail to scale up as more players join. Rescaling preserves the
  boss's current health *percentage* (not absolute HP) across each rescale
  so a boss at 40% doesn't jump to 40% of a *smaller* number and effectively
  lose health, or to 40% of a bigger number and gain HP out of nowhere
  relative to damage already dealt.
- **Bounty Hunt's "progress per account for current event" (spec, EVENT 5)
  is read as "get credited once per completion of the whole event", not "each
  account must personally land all 3 kills"**: the spec also says the event
  is a single shared instance ("3/3 targets"), which reads as one shared
  objective, not N parallel per-account 3/3 trackers over the same 3
  spawned creatures (which isn't physically possible — there's only one of
  each target). Whoever lands at least one of the three kills is registered
  as a participant and rewarded when the event succeeds. Flagged as a
  judgment call, not confirmed with the user.
- **Caravan Escort's ambush points are computed relative to the caravan's
  current position at the moment a progress threshold is crossed**, not
  fixed waypoints along the route: the caravan travels via
  `MotionMaster::MovePoint` with core pathfinding (`generatePath = true`
  default), so its exact route/midpoints aren't known in advance without
  duplicating that pathfinding — reading the live position when a threshold
  fires is simpler and always correct by construction.
- **Rare Hunt and Bounty Hunt do not use `OnKillRewarded`/`KillRewarder`
  like Random World Boss does**: both are read as solo/small-group content
  (a "hunt", not a raid target) per spec's own framing, so the simpler
  single-killer `OnCreatureKilled` path (Phase 7.1's mechanism) was reused
  rather than adding raid-credit semantics the spec didn't ask for here.
- **Phase 7.3 adds `WorldEvent::OnItemLooted`/`NotifyItemLooted` (fed from
  `PLAYERHOOK_ON_LOOT_ITEM`) and `WorldEvent::TryRewardPlayer`**, because
  Treasure Hunt and Resource Rush don't fit the "one shared pass/fail
  resolution, reward everyone registered" shape every earlier Phase 7 event
  used. Spec's own wording is per-account/per-action for both ("each
  account: one reward per event/day", "on completion: remove 10, grant
  completion, grant reward" — a personal threshold, not a group objective).
  Forcing them through `GrantRewardsToParticipants`/`OnSuccess()` would have
  meant inventing a fake "the whole event succeeded" moment that doesn't
  exist in the spec. `TryRewardPlayer` factors out the
  level+daily-limit+grant logic `GrantRewardsToParticipants` already had
  (which now calls it internally, once per participant) so both reward
  shapes share one code path with no behavior change for existing events.
- **Resource Rush's 60-second node respawn uses core's own GameObject
  respawn timer** (`Map::SummonGameObject`'s `respawnTime` parameter, which
  `SetRespawnTime()`s the object — confirmed by reading
  `Map::SummonGameObject` in `src/server/game/Entities/Object/Object.cpp`),
  not a custom despawn/respawn scheduler. The object is a genuinely
  temporary summon (`SetSpawnedByDefault(false)`, no DB row written), so
  this needed no extra bookkeeping beyond tracking its `ObjectGuid` — the
  same guid persists across the object's own respawn cycle.
- **Resource Rush counts a player's fragments via
  `Player::GetItemCount`/`DestroyItemCount` on the real inventory item**,
  not a separate in-memory or DB counter: the spec explicitly frames it as
  an item ("Item 920770 Meteor Fragment") a player physically holds and
  hands in, so the inventory *is* the counter — a shadow counter would just
  be a second source of truth to keep in sync with actual pickups/trades/
  deletions for no benefit.
- **Treasure Hunt/Resource Rush don't call `RegisterParticipant`**: that
  mechanism exists to answer "who gets rewarded when the shared objective
  resolves", which doesn't apply here — reward happens immediately per
  action via `TryRewardPlayer`. One consequence, flagged in
  phase-status.md: `.mevent complete <player> treasure` (which routes
  through the generic `ForceComplete` → `OnSuccess()`) does not itself
  grant a reward for these two events, unlike City Defense/Caravan/etc.
  Not "fixed" with a special case, since `.mevent complete`'s job (force
  the shared objective) has no shared objective to force here — the
  per-chest/per-hand-in reward already happened at the real moment it was
  earned.
- **Portal Event has no "protect an NPC" objective like City Defense's
  Captain**: the spec's own EVENT 6 text lists only a portal marker and 3
  waves culminating in a boss kill, with no defended entity mentioned —
  unlike EVENT 1's explicit Captain/failure-on-Captain-death design.
  Failure is timeout-only, matching what the spec actually specifies for
  this event rather than importing City Defense's shape by assumption.
- **Phase 7.4 adds five more `WorldEvent` hook pairs**
  (`OnCreatureSpawned`, `OnDungeonCompleted`, `OnFishingAttempt`,
  `OnPvpKill`, `OnGossipAction`) rather than trying to force Server Wide
  Event/Corrupted Zone/Dungeon Event/Fishing Frenzy/World PvP Event through
  the six hooks Phases 7.1-7.3 already had. Each of the five needed a
  mechanic no earlier event touched (a zone/map-wide passive spawn buff, a
  dungeon-completion signal, a fishing-specific roll, PvP kills, an NPC
  gossip menu) — inventing a generic "catch-all event hook" ahead of time
  would have meant guessing its shape before any concrete need existed.
  The registry/base-class split from Phase 7.1 is exactly what made adding
  five more events in one sub-phase not require touching
  `WorldEventsMgr`'s scheduler, GM commands, or playerbot dispatch at all —
  only new hook declarations plus the scripts that feed them.
- **Corrupted Zone/Dungeon Event apply their health/damage buff at spawn
  time (`AllCreatureScript::OnCreatureAddWorld`), not via a periodic zone
  scan**: the project's own performance rules explicitly discourage
  "global scans every tick"; a spawn hook is O(1) per creature that
  actually enters the world, with no scan at all. Trade-off, documented in
  phase-status.md: a creature already alive in the zone/dungeon when the
  event starts is not retroactively buffed. Adding a one-time
  start-of-event scan to close that gap was considered and rejected —
  it's still an unrequested scope addition (the spec doesn't ask for
  retroactive buffing), and the spawn-hook behavior is the natural,
  zero-cost default.
- **The damage buff uses `Unit::ApplyStatPctModifier(UNIT_MOD_DAMAGE_
  MAINHAND/OFFHAND/RANGED, TOTAL_PCT, pct)`**, a genuine, verified public
  Unit API (confirmed in `src/server/game/Entities/Unit/Unit.h`), not a
  guessed spell id or a fabricated stat field. `DamageMultiplier` from
  config (e.g. `1.15`) is converted to a percent bonus (`(1.15-1)*100 =
  15`) before being applied, matching the additive semantics of
  `TOTAL_PCT`.
- **`CorruptedZone.ZoneId` and `FishingFrenzy.ZoneId` default to `0`
  (disabled)**, unlike `DungeonEvent.MapIds` which shipped with real,
  verified values: this repo's own `mod-dungeon-clear` module already had
  the 5 dungeon map ids confirmed against this project's WotLK 3.3.5a data
  (`DungeonEventTables.h`), so reusing them isn't a guess. No equivalent
  confirmed source existed in this session for Icecrown's or Grizzly
  Hills' DBC zone id, and zone ids (unlike continent map ids, which are
  few and well-known) are numerous and easy to misremember — same
  "don't guess unverifiable game data" posture as every prior phase's
  creature/item entries.
- **Server Wide Event's Quartermaster is a persistent, GM-placed NPC, not
  summoned by `OnStart`/despawned by `OnStop`** like every combat event's
  creatures: the spec frames it as a fixture in Dalaran players return to
  repeatedly across many events/days, not a one-shot spawn tied to a
  single event's lifecycle. Its gossip script (`npc_war_effort_
  quartermaster`) is written and ready, but only takes effect once a GM
  sets `creature_template.ScriptName` on its row — the same "code is ready,
  data is the GM's job" split used throughout Phase 7.
- **World PvP Event's "same victim only once per event" is a single global
  `std::set<ObjectGuid>`**, not a per-killer set: the spec's anti-farm
  framing ("same account = no credit", "same victim only once per event")
  reads as closing farming loopholes broadly, and a global read is the
  stricter, more anti-farm-friendly interpretation — once a victim has
  contributed to *anyone's* count, they stop being farmable by *anyone*
  else too, not just by their original killer. Flagged as a judgment call,
  not confirmed with the user.
- **`MinRealParticipants` gates kill credit itself, not event start**: GM
  manual start (`.mevent start worldpvp`) has no participant-count
  precondition anywhere else in this framework (City Defense, Portal, etc.
  all start on GM command regardless of who's nearby), so gating start the
  same way here would have been inconsistent; instead, a kill only counts
  toward the objective if the live participant count in the arena radius
  meets the threshold at that moment — reads as "this needs to actually be
  a contested fight, not a 1-on-1 gank," which is what the spec's own
  placement of that config key next to `RequiredUniqueKills` (an objective
  parameter, not a scheduler parameter) suggests.
- **`WorldEvent::Start()` must not force `Active` after `OnStart()`**: found
  during post-implementation SOAP runtime verification of all 13 events.
  `Start()` called `OnStart()` then unconditionally
  `SetState(WorldEventState::Active)`, silently overwriting a `Failed`
  state an event's own `OnStart` had just set (Corrupted Zone/Fishing
  Frenzy refusing to start with `ZoneId = 0` were the two events that
  exposed it — both reported "started" and ran anyway). Fixed by only
  advancing to `Active` when the state isn't already `Failed`. Applies to
  every current and future event uniformly since it's in the shared base
  class, not per-event code.
- **Icecrown = zone 210, Grizzly Hills = zone 394**: confirmed (not
  guessed) from this repo's own shipped
  `data/sql/base/db_world/graveyard_zone.sql`, whose graveyard-name
  comments (`"... - Icecrown"`, `"... - Grizzly Hills"`) are tied to those
  zone ids. Used to fill in `WorldEvents.CorruptedZone.ZoneId` /
  `WorldEvents.FishingFrenzy.ZoneId`, previously left at the disabling
  default of `0` in 7.4 for lack of a verified source.
- **Live `mod_server_activities.conf` was stale**, not a Phase 7 bug: it
  shipped from an early phase (10 of 33 documented keys) and was never
  redeployed as later phases added config blocks. All present keys already
  matched the compiled-in defaults, so this never changed behavior — but
  `ConfigMgr::GetOption` logs an uncached warning on every miss, and
  `ServerActivitiesExplorationScript`'s hook fires on every player position
  update, so under playerbot load it flooded `Server.log`. General lesson:
  a partially-deployed `.conf` next to a fully up-to-date `.conf.dist` is a
  silent log-spam risk even when it causes no functional difference —
  worth diffing key counts after any phase that touches a `.conf.dist`
  this feature already has deployed live.
