# Server Activities & Mount Roulette System — Overview

Two static AzerothCore modules (WotLK 3.3.5a):

- **mod-mount-roulette** — owns the account-scoped spins/shards/pity balance
  (`characters`.`mod_mount_roulette_account`) and exposes it as a public API
  (`MountRouletteMgr`, `sMountRouletteMgr`) other modules can call. Currently
  only the balance API and GM commands exist; the roulette spin itself (RNG,
  pity, rewards) is Phase 3 scope and not implemented yet.
- **mod-server-activities** — the Activity Manager. Gates activities by
  level/bot status, tracks a lazy per-character daily limit
  (`characters`.`mod_server_activities_daily`), and credits spins through
  `MountRouletteMgr::AddSpins`. Currently implements one activity:
  Battleground Victory.

Dependency direction: mod-server-activities → mod-mount-roulette (one way).
Both modules are discovered automatically by AzerothCore's `modules/*` glob;
no CMake/registration list changes were needed.

Plan: `plan/plan-server-activities-mount-roulette-system.md`.
PRD: `docs/prd-server-activities-mount-roulette-system.md`.
