# Server Activities & Mount Roulette System — Overview

Two static AzerothCore modules (WotLK 3.3.5a):

- **mod-mount-roulette** — owns the account-scoped spins/shards/pity balance
  (`characters`.`mod_mount_roulette_account`) and exposes it as a public API
  (`MountRouletteMgr`, `sMountRouletteMgr`) other modules can call. Now also
  owns the roulette spin itself: pity-aware rarity RNG, mount/shard reward
  resolution, and the account-scoped mount collection
  (`characters`.`mod_mount_roulette_collection`). Phase 4 adds a player-facing
  UI bridge (`.roulette spin|info|collection` + a client addon) built on
  AzerothCore's built-in addon-command channel — no AIO/third-party code
  (see `decisions.md`).
- **mod-server-activities** — the Activity Manager. Gates activities by
  level/bot status, tracks a lazy per-character daily limit
  (`characters`.`mod_server_activities_daily`), and credits spins through
  `MountRouletteMgr::AddSpins`. Implements: Battleground Victory, Dungeon,
  Heroic, Raid Boss, Achievement (Phase 2), Exploration, Profession, Fishing
  (Phase 6); World Event/World Boss are credited externally by
  mod-world-events through the same entry point.

- **mod-world-events** (Phase 5) — a single scripted event, `"invasion"`:
  waves → elites → boss, spawned via `Map::SummonCreature` on a configured
  continent map/point and tracked by `ObjectGuid` (no stored `Creature*`).
  Advances a stage when its tracked summons are all dead, or force-advances
  on a per-stage timeout. `.mevent start|stop invasion` (GM), plus an
  optional random auto-start roll on an accumulator (not a per-tick scan).
  Boss kill credit routes through `ServerActivitiesMgr::CreditActivity`
  (`"worldevent"` / `"worldboss"` activity ids) — no new table.

Dependency direction: mod-server-activities → mod-mount-roulette (one way);
mod-world-events → mod-server-activities (one way, for kill credit only).
All three modules are discovered automatically by AzerothCore's `modules/*`
glob; no CMake/registration list changes were needed.

Plan: `plan/plan-server-activities-mount-roulette-system.md`.
PRD: `docs/prd-server-activities-mount-roulette-system.md`.
