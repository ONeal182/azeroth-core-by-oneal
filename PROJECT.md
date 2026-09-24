# PROJECT.md — stable context

Load on demand (see tier table in `AGENTS.md`). Workflow rules live in `.agents/skills/azerothcore/SKILL.md`.

## Layout

- `src/` core · `modules/` modules (`/modules/*` is gitignored; many modules are their own git repos)
  · `data/sql/` migrations · `.agents/` skills, docs, plans.
- DBs: `acore_auth`, `acore_characters`, `acore_world`.
- Build: `build/` (MSVC, RelWithDebInfo), target `worldserver`. Added a `.cpp`? Run `cmake .` in `build/` first.
- Runtime: `C:\azerothcore\server\` — `worldserver.exe`, `configs/`, `configs/modules/`,
  logs `Server.log`, `Errors.log`, `MountRoulette.log`.
- MySQL CLI: `C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe` (Git-Bash's bundled mysql does not run).
- Active custom modules: `mod-server-activities`, `mod-mount-roulette`, `mod-world-events`.
  Also installed: playerbots, `mod-dungeon-clear`, transmog, others — check `modules/`.

## Priorities

Correctness > preserve behavior/architecture > reuse existing mechanism > smallest change > evidence-backed claims.
Edit core only when no hook/extension point fits.

## Known gotchas (verified)

- Module SQL under `modules/*/data/sql/db-*/` is auto-applied by the worldserver updater at startup and tracked in
  the `updates` table (name + SHA1). Applying it by hand too → duplicate key → world DB update fails
  → server exits.
  If applied by hand, insert its `updates` row (`state='MODULE'`).
- Modules link as a static lib: a self-registering static object in a `.cpp` nothing references is dropped by the
  linker. Register through an explicit function called from the module loader.
- Many GM commands are `Console::No` (`.go xyz`, `.npc add`, `.respawn`, self `.tele`) — unusable via SOAP.
  Console-safe: `.tele name <player> <loc>`, `.player learn <player> <spell>`, `.character level <player> <n>`,
  `.achievement add <id> <player>`.
- New creature spawns appear only after a server restart.
- A key missing from a live `.conf` logs "Missing property" on every read —
  keep live configs in sync with `.conf.dist`.
- WotLK `CurrencyTypes.dbc` / `ItemExtendedCost.dbc` are client-side: no new currencies or token-vendor costs without
  a client patch. Reuse existing DBC rows or use gossip-driven logic.

## Playerbots

Part of normal operation. Account for bot sessions; use existing bot checks (`WorldSession` / playerbot APIs);
never break PlayerbotAI; no parallel bot detection.

## BOT_BOT invariants

- Bot–bot interaction only while an eligible real human observer is nearby (same map/instance/phase, visible,
  in range). Online elsewhere is not eligible. Observer permits interaction; it never triggers it.
- Observer lost → stop new module-owned actions, clean up at a safe boundary; started indivisible core ops may finish.
- Real game actions only. No bot–bot chat, LLM dialogue, or fake text emotes. Talking to real players is fine.
- Normal PlayerbotAI and unrelated world systems run without observers.

## Database

Pick the right DB; copy an existing module migration pattern; verify schema first; no destructive migrations
without approval.

## Performance / lifetime

Hot paths: update ticks, combat, movement, Player/Unit/Creature, playerbots, large scans. Avoid per-tick DB
queries, global scans, O(n²), hot-path log spam, recomputing stable data. Do not hold world-object pointers across
callbacks/events/map changes — store `ObjectGuid` and reacquire.

## Compatibility

Keep config keys/semantics, public module APIs, schema contracts, persisted enum values, commands, data formats —
unless the task requires a break; then state migration steps.
