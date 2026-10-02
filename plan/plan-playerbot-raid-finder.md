# Plan: mod-playerbot-raid-finder

Status: PLAN (implementation not started). Target: AzerothCore WotLK 3.3.5a + mod-playerbots.

## 0. Verdict

The feature can be built as a **standalone module with zero core changes and zero
mod-playerbots changes for the MVP**. It links into the shared `modules` static
library next to mod-playerbots, the same way `mod-dungeon-clear` already does
(precedent: `modules/mod-dungeon-clear/src/DungeonQueueFill/*`).

Two optional, small mod-playerbots patches are listed for Phase 2 (offline random-bot
login, ToC raid strategy). No core patch is planned at all.

## 1. Existing architecture (reused)

### AzerothCore core

| Need | Existing API | Location |
|---|---|---|
| Raid group | `Group::Create(Player*)`, `AddMember(Player*, uint8 roles)`, `RemoveMember(...)`, `ChangeLeader`, `ConvertToRaid()`, `Disband()` | `src/server/game/Groups/Group.h:202-261` |
| Raid size/difficulty | `Group::SetRaidDifficulty(Difficulty)`, `Player::GetRaidDifficulty()` | `Group.h:281`, `Player.h:1951` |
| Main tank flag | `Group::SetGroupMemberFlag(guid, true, MEMBER_FLAG_MAINTANK)` | `Group.h:75,271` |
| Lockouts | `sInstanceSaveMgr->PlayerGetBoundInstance(guid, mapId, diff)`, `PlayerGetBoundInstances` | `Instances/InstanceSaveMgr.h:207-209` |
| Final entry gate | `sMapMgr->PlayerCannotEnter(mapId, player)` returning `Map::EnterState` (`CANNOT_ENTER_INSTANCE_BIND_MISMATCH`, `NOT_IN_RAID`, `MAX_PLAYERS`, `ZONE_IN_COMBAT`, ...) | `Maps/MapMgr.h:141`, `Maps/Map.h:276-286` |
| Level / ilvl requirement | `sObjectMgr->GetAccessRequirement(mapId, diff)` (`dungeon_access_template`: ICC/Ulduar/Naxx/ToC = min level 80, `min_avg_item_level` 0), `Player::GetAverageItemLevel()` | `ObjectMgr.h:885`, `Player.h:2616` |
| Raid entrance coords | `sObjectMgr->GetMapEntranceTrigger(mapId)` (`areatrigger_teleport`). Note: `lfg_dungeon_template` has **no** raid rows. | `ObjectMgr.h:901` |
| Teleport in/out | `Player::SetEntryPoint()`, `TeleportTo(...)`, `TeleportToEntryPoint()` (same pattern as `LFGMgr::TeleportPlayer`) | `DungeonFinding/LFGMgr.cpp:2228` |
| Hooks | `GroupScript::OnAddMember/OnRemoveMember/OnDisband`; `PlayerScript::OnPlayerLogout/OnPlayerMapChanged/OnPlayerGossipSelect/OnPlayerCanJoinLfg/OnPlayerBeforeSendChatMessage`; `WorldScript::OnUpdate`; `ServerScript::CanPacketReceive/CanPacketSend`; `CommandScript` | `Scripting/ScriptDefines/*.h` |

Core LFG for raids: `LFGMgr::JoinLfg` treats `LFG_TYPE_RAID` as **Raid Browser only**
(`JoinRaidBrowser`, `LFG_STATE_RAIDBROWSER`, `LFGMgr.cpp:815`). There is no raid
matchmaking, proposal, or teleport. Therefore the stock LFG queue is **not** reused for
matchmaking. It is reused only as a UI entry point (Phase 2, section 9).

### mod-playerbots (all public, no patch)

| Need | Existing API | Location (`modules/mod-playerbots/src/`) |
|---|---|---|
| Online random-bot pool | `sRandomPlayerbotMgr.GetAllBots()` (copy of guid→Player*), `IsRandomBot(Player*)` | `Bot/RandomPlayerbotMgr.h:124`, `.cpp:2133` |
| Bot AI access | `GET_PLAYERBOT_AI(player)` → `PlayerbotAI*` | `Bot/PlayerbotAI.h` |
| Role by spec | `AiFactory::GetPlayerRoles(Player*)` → `BotRoles` (TANK=1, HEALER=2, DPS=4), `GetPlayerSpecTab`; `PlayerbotAI::IsTank/IsHeal/IsRanged/IsMelee(Player*, bool bySpec=true)` | `Bot/Factory/AiFactory.h:31-33`, `PlayerbotAI.h:425-439` |
| Gear | `PlayerbotAI::GetMixedGearScore(Player*, ...)`, `GetEquipGearScore` | `PlayerbotAI.h:532-534` |
| Master/follow | `UpdateAIGroupMaster()` + `FindNewMaster()`: a random bot in a group with a real player auto-takes the real player as master and adds `+follow` | `PlayerbotAI.cpp:413, 4427` |
| Strategy reset as on invite | `ResetStrategies()`, `ChangeStrategy("+follow,-lfg,-bg", BOT_STATE_NON_COMBAT)`, `Reset()` (mirrors `AcceptInvitationAction`) | `AcceptInvitationAction.cpp:16-66` |
| Raid AI | `ApplyInstanceStrategies(mapId)` runs automatically on far-teleport ack: 533→`naxx`, 603→`ulduar`, 631→`icc`. **649 (ToC) has no strategy** (generic tank/heal/dps AI). | `PlayerbotAI.cpp:800, 1631-1773` |
| Release | No group + random bot → `SetMaster(nullptr); Reset(true); ResetStrategies()` automatically; `ProcessBot` resumes random lifecycle | `PlayerbotAI.cpp:425-433`, `RandomPlayerbotMgr.cpp:1392` |
| Post-release refresh | `sRandomPlayerbotMgr.Refresh(Player*)`, `RandomTeleportForLevel(Player*)`, `ScheduleTeleport(guid)` | `RandomPlayerbotMgr.cpp:2086`, `.h:115,133` |
| Optional respec | `PlayerbotFactory::InitTalentsBySpecNo(bot, specNo, reset)` + `ResetStrategies()` | `Bot/Factory/PlayerbotFactory.cpp:1572` |
| Command precedent | `playerbots_commandscript` | `Script/PlayerbotCommandScript.cpp:17` |
| Addon channel precedent | `OnPlayerBeforeSendChatMessage` + `LANG_ADDON` | `mod-dungeon-clear/src/DungeonClearAddonHook.cpp` |

Known behaviours the module must respect:
- `ProcessBot(Player*)` makes a bot leave a non-LFG group **led by a random bot**
  (`RandomPlayerbotMgr.cpp:1481-1487`). The leader must always be a real player.
- `GetAllBots()` returns a copy; a `Player*` may dangle after logout. Always re-resolve
  by GUID (`ObjectAccessor::FindPlayer`).
- A grouped random bot is never logged out by `ProcessBot` (`.cpp:1344`), so a bot in a
  Raid Finder group stays online until released.
- Chat-invite path (`PlayerbotSecurity::LevelFor`) is bypassed: the module adds bots
  with `Group::AddMember` directly, so faction, level and gear checks are done by the
  module itself.

## 2. What is missing

1. Raid queue (per raid definition and team), role selection, cancel.
2. Matchmaker: real players first, wait `BotFill.Delay`, then fill from bots.
3. Bot candidate filter with logged reject reasons (level, online, group, BG/arena,
   instance, LFG state, lockout, role, gear, faction).
4. Raid assembly: group creation with a real leader, difficulty, main tank flags.
5. Accept/decline step with partial replacement.
6. Teleport orchestration (player first, bots after the instance is created).
7. Session tracking: leaves, logouts, disband, raid end, bot release and evacuation
   from the raid map (playerbots does not teleport a released bot out of an instance).
8. Configurable raid definitions, status output, GM commands, matchmaking logs.
9. UI (gossip/command in MVP, addon in Phase 2).
10. ToC raid strategy (out of scope; generic AI is used).

## 3. Proposed architecture

Module `modules/mod-playerbot-raid-finder/`. CMake mirrors `mod-dungeon-clear`:
requires mod-playerbots and includes its `src/`.

```
src/
  RfConfig.{h,cpp}             conf values (sConfigMgr), reload
  RfRaidRegistry.{h,cpp}       RaidDefinition loader (world DB table, conf fallback)
  RfRoles.{h,cpp}              role detection for players and bots
  RfCompositionPlanner.{h,cpp} engine-free slot arithmetic (unit-testable)
  RfBotSelector.{h,cpp}        candidate scan, filters, reject reasons, scoring
  RfQueue.{h,cpp}              queue entries per (raidKey, team)
  RfSession.{h,cpp}            one raid being formed/run: state machine
  RfManager.{h,cpp}            owns queue and sessions, tick, admission, debug flag
  RfHooks.cpp                  WorldScript / PlayerScript / GroupScript glue
  RfCommands.cpp               .rf command table
  RfGossip.cpp                 player-sourced gossip UI and accept popup
  mod_playerbot_raid_finder_loader.cpp
conf/mod_playerbot_raid_finder.conf.dist
data/sql/db-world/base/raid_finder_definition.sql
```

Threading: everything runs on the world thread (`WorldScript::OnUpdate`, packet and
command handlers). `OnWorldUpdate` runs after `sMapMgr->Update` (`World.cpp:1245,1346`),
so map workers are idle. Sessions store GUIDs only; `Player*` is resolved every tick.

Key types:
- `RaidDefinition { key, name, mapId, difficulty, size, tanks, healers, dps, minRanged,
  minLevel, minAvgItemLevel, maxBots, entrance override, enabled }`
- `QueueEntry { playerGuid, team, raidKey, role, joinTime }`
- `RfSession { id, raidKey, team, leaderGuid, slots[] {guid, role, isBot, state},
  stage, stageTimer }`

### Session state machine

```
Searching -> FillingBots -> Assembling -> Proposal -> Teleporting -> InRaid -> Releasing -> Done
   (every timeout or fatal error goes to Releasing)
```

- **Searching**: real players are collected. Wait until real slots are full, or until
  `BotFill.Delay` elapsed and `MinRealPlayers` is reached.
- **FillingBots**: `RfBotSelector` picks bots for missing roles. On failure the reason is
  logged and the session retries every `BotFill.RetryInterval` until `QueueTimeout`.
- **Assembling**: leader is a real player. `Group::Create(leader)` if needed,
  `ConvertToRaid()`, `SetRaidDifficulty()`, `AddMember()` per member,
  `MEMBER_FLAG_MAINTANK` on tanks, bot strategy reset as in `AcceptInvitationAction`.
- **Proposal**: real players get the accept popup; bots are auto-accepted. Decline or
  timeout removes that member and reopens the slot; the matchmaker tries a queued player
  first, then a bot. The raid survives while at least one real player remains.
- **Teleporting**: real players: `SetEntryPoint()` + `TeleportTo(entrance)`. Bots
  teleport only after the leader's `OnPlayerMapChanged` reports the raid map (instance
  exists and is bound to the group), `Teleport.BotsPerTick` per tick. Each bot first
  passes `sMapMgr->PlayerCannotEnter`; failure replaces the bot.
- **InRaid**: hooks watch membership. A lost bot is optionally refilled. When no real
  player is in the group, or none is on the raid map for `InRaid.AbandonTimeout`, go to
  Releasing.
- **Releasing** (single funnel): per bot `RemoveMember`, `TeleportToEntryPoint()` (or
  homebind), `sRandomPlayerbotMgr.Refresh(bot)`, `ScheduleTeleport(guid)`. playerbots
  `UpdateAIGroupMaster` then clears master and restores random strategies.

## 4. Data flow

```
.rf join ICC10 dps  (or gossip / addon)
 -> RfManager::Join: validate level, ilvl, lockout, BG/LFG state, existing session
 -> RfQueue entry                                    [log: player, role, raid]
WorldScript::OnUpdate
 -> matchmaker per (raidKey, team): oldest real players first, role caps
 -> after BotFill.Delay: RfCompositionPlanner computes deficit
 -> RfBotSelector over GetAllBots()                  [log: considered/rejected/picked]
 -> Assembling: Create / ConvertToRaid / SetRaidDifficulty / AddMember
 -> Proposal: popup to players, bots auto-accept, decline -> replace
 -> Teleporting: players TeleportTo(entrance); leader on map -> bots TeleportTo
 -> bot HandleTeleportAck -> ApplyInstanceStrategies(mapId) -> naxx / ulduar / icc
 -> InRaid: hooks watch membership                   [log: final composition]
 -> Releasing: bots removed, evacuated, Refresh -> random lifecycle resumes
```

## 5. Bot selection (RfBotSelector)

Source (MVP): `sRandomPlayerbotMgr.GetAllBots()`, online random bots only.
Filters in order; each rejection is counted, and logged per bot when debug is on:

| Code | Check |
|---|---|
| `NOT_RANDOM` | `!IsRandomBot(bot)` |
| `NOT_IN_WORLD` | `!IsInWorld()`, `IsBeingTeleported()`, session logging out |
| `FACTION` | team differs (unless `CrossFaction`) |
| `LEVEL` | below `minLevel` |
| `GROUPED` | `GetGroup()` not null |
| `BG` | `InBattleground()`, `InArena()`, `InBattlegroundQueue()` |
| `LFG` | `sLFGMgr->GetState(guid) != LFG_STATE_NONE` |
| `INSTANCE` | `GetMap()->Instanceable()` |
| `BUSY` | dead, in flight, in combat, claimed by another session |
| `LOCKOUT` | `PlayerGetBoundInstance(guid, mapId, diff)` exists |
| `ROLE` | `AiFactory::GetPlayerRoles(bot)` lacks the needed role |
| `GEAR` | `GetAverageItemLevel()` below the raid or global minimum |

Roles: bots use `AiFactory::GetPlayerRoles` (spec-tab based; Paladin, Druid, DK,
Warrior, Priest, Shaman handled). A multi-role bot (feral TANK|DPS) fills one slot. Its
existing default combat strategies already match the spec. Real players declare their role.
Scoring (MVP): higher gear, then closer level. Phase 2 adds composition scoring.

## 6. Configuration

`conf/mod_playerbot_raid_finder.conf.dist`:

```
RaidFinder.Enable = 1
RaidFinder.UpdateInterval = 1000          # ms
RaidFinder.BotFill.Enable = 1
RaidFinder.BotFill.Delay = 30             # s to wait for real players
RaidFinder.BotFill.RetryInterval = 15     # s
RaidFinder.MinRealPlayers = 1
RaidFinder.MaxBotsPerRaid = 24
RaidFinder.MinimumAvgItemLevel = 0        # global floor; higher per-raid value wins
RaidFinder.PreferRealPlayers = 1
RaidFinder.RequireRoleBalance = 1         # 0: other roles may fill dps when short
RaidFinder.QueueTimeout = 1800            # s
RaidFinder.Proposal.Timeout = 60          # s
RaidFinder.Proposal.Replace = 1
RaidFinder.AutoTeleport = 1
RaidFinder.Teleport.BotsPerTick = 5
RaidFinder.InRaid.RefillBots = 1
RaidFinder.InRaid.AbandonTimeout = 300    # s
RaidFinder.MaxConcurrentSessions = 10
RaidFinder.CrossFaction = 0
RaidFinder.Debug = 0
RaidFinder.Definitions.Source = db        # db | conf
```

World table `raid_finder_definition` (reload: `.rf reload`): `key` PK, `name`, `map_id`,
`difficulty`, `size`, `tanks`, `healers`, `dps`, `min_ranged`, `min_level`,
`min_avg_item_level`, `max_bots`, `entrance_map/x/y/z/o` (NULL = areatrigger), `enabled`.

| key | map | diff | size | T | H | D |
|---|---|---|---|---|---|---|
| NAXX10 | 533 | 0 | 10 | 2 | 2 | 6 |
| NAXX25 | 533 | 1 | 25 | 2 | 5 | 18 |
| ULD10 | 603 | 0 | 10 | 2 | 2 | 6 |
| ULD25 | 603 | 1 | 25 | 2 | 5 | 18 |
| TOC10 | 649 | 0 | 10 | 2 | 2 | 6 |
| TOC25 | 649 | 1 | 25 | 2 | 5 | 18 |
| ICC10 | 631 | 0 | 10 | 2 | 2 | 6 |
| ICC25 | 631 | 1 | 25 | 2 | 5 | 18 |

Conf fallback: `RaidFinder.Definition.ICC10 = "631 0 10 2 2 6"`. Load validation:
`tanks + healers + dps == size`, `MapEntry::IsRaid()`, difficulty valid, entrance found.

## 7. UI

### MVP (no client changes)
- Player commands: `.rf join <KEY> <tank|heal|dps>`, `.rf leave`, `.rf status`,
  `.rf list`, `.rf accept`, `.rf decline`.
- `.rf` with no arguments opens a **player-sourced gossip menu** (raid list → role →
  join; status; cancel). Selections arrive through `PlayerScript::OnPlayerGossipSelect`.
- Accept dialog: gossip menu with a confirmation box ("Raid ICC 10 is ready. Enter?"),
  plus `.rf accept` / `.rf decline` as a fallback.
- Status text (also pushed on every change):

```
[Raid Finder] ICC 10 - Filling with bots
Tank: 1/2  Heal: 1/2  DPS: 3/6
Real players: 2  Bots selected: 3
```

### Phase 2 options
- **A. Native LFR window, no client patch.** In the stock 3.3.5 client the Raid tab of
  the LFG frame sends `CMSG_LFG_JOIN` with raid dungeon ids and roles. Core calls
  `sScriptMgr->OnPlayerCanJoinLfg(player, roles, dungeons, comment)` **before** the raid
  branch (`LFGMgr.cpp:614`). The module returns `false` for raid ids it serves and puts the
  player into its own queue. "Leave" is caught via `ServerScript::CanPacketReceive`
  (`CMSG_LFG_LEAVE`). Limits: no native role/count readout for raids and no native raid
  proposal popup, so status still goes through chat or the addon. Needs a live client test
  before committing to it.
- **B. Addon "RaidFinder" (preferred UI).** Blizzard-style frame (reuse `PVEFrame`/
  `LFDQueueFrame` textures and templates): raid dropdown, role check boxes with LFG role
  icons, Find/Leave buttons, live counters, ready popup reusing `LFDDungeonReadyDialog`
  style. Transport: addon prefix `RF`, client → server through `SendAddonMessage` parsed in
  `OnPlayerBeforeSendChatMessage` (precedent: `DungeonClearAddonHook.cpp`), server →
  client through `CHAT_MSG_WHISPER`/`LANG_ADDON` packets. Server protocol is the same
  `RfManager` API as the commands, so the addon is purely a view.

## 8. Logging

Logger `module.raidfinder` (appender configured in worldserver.conf). Messages:
- `JOIN player=Name role=DPS raid=ICC10 team=A ilvl=245`
- `LEAVE player=Name reason=cancel|logout|timeout`
- `SESSION #7 ICC10 created; real T1 H0 D1; need T1 H2 D5`
- `SCAN #7 considered=412 rejected: GROUPED=120 LEVEL=200 ROLE=60 LOCKOUT=3 ...`
- debug: `REJECT #7 bot=Name reason=LOCKOUT detail=instance 1234`
- `PICK #7 bot=Name class=Paladin role=HEAL ilvl=232`
- `FORMED #7 leader=Name comp: T2 H2 D6 (melee 3 ranged 3) bots=8`
- `FAIL #7 reason=not enough HEAL candidates (0/2)` / `PROPOSAL #7 Name declined, replacing`
- `RELEASE #7 bots=8 reason=raid abandoned`

## 9. GM / debug commands (SEC_GAMEMASTER)

| Command | Purpose |
|---|---|
| `.rf queue` | all queue entries with wait time |
| `.rf sessions` | sessions with stage, composition, member list |
| `.rf bots <KEY> [team]` | dry-run candidate scan: counts per reject reason and best picks per role, no claiming |
| `.rf force <KEY> [player]` | skip `BotFill.Delay` for that session or create one for player |
| `.rf release <id>` | force a session into Releasing |
| `.rf clear` | release every session and empty the queue |
| `.rf debug on/off` | per-bot reject logging |
| `.rf reload` | reload conf and definitions (only when no session is active, else refuse) |

## 10. Files and modules touched

| Area | Change |
|---|---|
| AzerothCore core | **None.** All hooks and APIs above already exist. |
| mod-playerbots (MVP) | **None.** Only public API is used. |
| mod-playerbots (Phase 2, optional) | (a) public `RandomPlayerbotMgr::LoginRandomBotForActivity(guid)` that does what `AddRandomBots` does for one bot (`SetEventValue(guid,"add",...)`, `currentBots.insert`, `AddPlayerBot(guid,0)`), so offline random bots can be used; (b) ToC raid strategy (new `RaidStrategyContext` entry + case 649 in `ApplyInstanceStrategies`), separate effort |
| New module | `modules/mod-playerbot-raid-finder/` (all code, conf, SQL, tests) |
| Client addon (Phase 2) | separate repo/folder `RaidFinder` addon |

## 11. Minimal viable implementation (phases)

Each phase builds and is verified before the next one starts.

1. **Skeleton**: module dir, CMake (copy `mod-dungeon-clear` playerbots linkage), loader,
   conf, `RaidFinder.Enable`, `.rf` command table with `status` only. Check: worldserver
   builds, `.rf status` answers.
2. **Definitions**: `raid_finder_definition` SQL + registry + validation + `.rf list`,
   `.rf reload`. Check: 8 rows load, bad row is rejected with log.
3. **Planner + roles**: `RfCompositionPlanner` (pure) + `RfRoles`. Unit tests (repo
   `src/test` gtest target) for ICC10 example: real T1+D1 → bots T1 H2 D5; ICC25; full;
   over-subscribed role.
4. **Bot selector**: filters, reject counters, `.rf bots ICC10`. Check live: dry-run
   lists candidates and reasons on a running server.
5. **Queue + session to Assembling**: `.rf join/leave`, single real player, session forms
   raid group with 9 bots, correct roles, main tank flags. Hooks for logout/leave.
6. **Proposal + teleport**: accept via `.rf accept` / gossip, player teleport, bots
   teleport after leader arrival, `PlayerCannotEnter` check. Check live: ICC10 entered,
   bots log `icc` strategy (`ApplyInstanceStrategies`, verify with bot `co ?`/`nc ?`).
7. **InRaid + release**: abandon detection, bot release, evacuation, `Refresh`. Check
   live: after `/leave` all 9 bots ungroup, leave map 631, random AI resumes.
8. **Gossip UI + status push + full logging**.

MVP acceptance = user story item 25: one real player, ICC10, chosen role, 9 bots,
correct composition, teleport, raid AI, release after exit.

## 12. Phase 2

- Multiple real players per session with real-first packing and decline replacement
  (core logic exists from MVP; this phase hardens and tests it).
- Offline random bots (mod-playerbots helper above).
- Composition quality scoring: melee/ranged balance (`IsRanged(bot,true)`,
  `def.minRanged`), Bloodlust/Heroism (Shaman), battle res (Druid, DK; Warlock soulstone),
  class buffs coverage, dispel types, interrupts. Implemented as a score in
  `RfBotSelector` used only to choose among valid candidates.
- Optional respec to fill a missing role (`InitTalentsBySpecNo` + `InitGlyphs` +
  `ResetStrategies`), off by default because gear is not changed.
- Native LFR entry point (option A) and Blizzard-style addon (option B).
- Refill bots mid-raid, lockout-aware "continue saved raid" for real players.
- ToC raid strategy in mod-playerbots.
- Heroic difficulties (definition rows only; validate access requirements).

## 13. Risks and open questions

- **Lockouts**: bots permanently bound to another instance of the same map/difficulty
  are filtered. Bots entering get the group bind; after the run they keep a lockout until
  reset, which shrinks the pool for that week. Option: unbind bots on release
  (`sInstanceSaveMgr->PlayerUnbindInstance`, verify API) behind a config flag.
- **Bot gear**: random bots at 80 may be below raid level. `MinimumAvgItemLevel` filters;
  if the pool is too weak, Phase 2 can call playerbots gear init. Not in MVP.
- **Pool size**: MVP needs enough online, idle, level-80 random bots of the right roles
  and faction. `.rf bots` shows real availability before testing.
- **Leader must stay real**: if the real leader leaves, leadership moves to another real
  player, else the session is released (playerbots makes bots leave random-bot-led groups).
- **ToC**: generic AI only until a strategy exists.
- **Option A UI** depends on client behaviour of the raid tab; must be checked live.
