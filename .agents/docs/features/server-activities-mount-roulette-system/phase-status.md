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

## Remaining phases

2. PvE and Achievement activities
3. Mount Roulette backend
4. AIO interface
5. World events framework + Invasion + World Boss
6. Exploration/Profession/Fishing activities
7. Remaining World Random Events
