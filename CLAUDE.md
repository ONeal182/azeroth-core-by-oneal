# AzerothCore Development Rules

## Project

- Customized AzerothCore WotLK 3.3.5a with PlayerBots and custom modules.
- Work from the `azerothcore-wotlk` repository root and prefer relative paths.
- Development scope includes **all of `modules/`**, not only PlayerBots.
- Main code: `src/common/`, `src/server/game/`, `src/server/shared/`, `src/server/database/`, `src/server/apps/worldserver/`, `modules/`.
- Respect the actual Windows/WSL environment; do not mix paths, binaries, or toolchains without verifying compatibility.

## Change policy

- Check `git status` before significant work and preserve existing/user changes.
- Change only what the current task requires; avoid unrelated refactors.
- Reuse existing AzerothCore/module mechanisms before creating new managers, schedulers, or parallel systems.
- Prefer module-level changes; modify core only when reasonably necessary.
- Do not delete functionality, add stubs, disable checks, comment out working behavior, or weaken validation merely to make a build/test pass.
- For complex multi-file work, give a short plan first; small edits do not need planning ceremony.
- Never commit/push, `git reset --hard`, `git clean -fd`, delete major directories, or perform broad rewrites unless explicitly requested.
- Do not change MCP configuration, hooks, permissions, API routing, model routing, or optimization tooling during ordinary development.
- Never expose secrets or place them in code, logs, reports, or Git.

## Tool selection

Choose the most precise tool for the question. This is **not** a mandatory chain.

- **AzerothMCP:** DB data/schema, NPCs, items, quests, SmartAI, conditions, waypoints, spell/data lookups, and available runtime checks. Prefer specialized tools, then narrow SQL only if needed.
- **clangd MCP:** exact C++ definitions, references, implementations, types, inheritance, call hierarchy, symbols, and diagnostics. If results look wrong, verify the compilation database/index.
- **Graphify:** subsystem/module relationships, dependencies, architecture, and impact analysis. Query only the relevant graph region. Paths through generic primitives such as `_string`, `string`, `uint32`, `uint8`, or `int32` are not meaningful architectural evidence; verify important C++ relationships with clangd/source.
- **Atlas CLI:** first-pass orientation in unfamiliar code. Use focused paths and ~800–1600 token budgets; do not run it before every edit.
- **ast-grep CLI:** structural C++ patterns and controlled bulk refactors. Restrict paths, inspect matches, and preview before rewriting.
- **rg/Grep:** literal strings, file names, config keys, SQL names, log messages, and quick exact searches.
- **Caveman:** use compacted output when sufficient; recover exact original fragments whenever correctness depends on omitted details.
- **ccache:** preserve an existing working integration; do not clear the cache. Inspect stats only when relevant.

Use only tools that are actually available and their real schemas/`--help`. If a tool is unavailable, fall back to targeted source search/read instead of repairing unrelated tooling. Empty index/search results do not prove that a symbol or dependency does not exist. Graphs, indexes, and diagnostics guide investigation but do not replace source, build, tests, or runtime verification.

## Installed workflow skills

Use installed skills only when they fit the task; do not invoke them mechanically.

- **prd:** define WHAT/WHY, scope, invariants, edge cases, and acceptance criteria without prescribing implementation.
- **plan-phase:** convert a PRD into small, verifiable AzerothCore implementation phases.
- **implement-phase:** implement and verify exactly one plan phase, then stop.
- **grill-me / grilling:** optional requirement/decision stress-testing before large, ambiguous, high-risk, or cross-cutting work.
- **tdd:** default workflow for executable behavior changes and bug fixes.
- **git-commit:** use only when the user explicitly asks to create a commit; never auto-commit.

Skills do not override project safety, scope, or verification rules.

## Context and token efficiency

- **Do not spawn subagents unless the user explicitly requests them.**
- Prefer Graphify, clangd, AzerothMCP, ast-grep, `rg`, and targeted reads in the main agent.
- If the relevant file/symbol is already known, investigate it directly; skip Atlas/Graphify when unnecessary.
- Start narrow and expand only when evidence is insufficient.
- Read only the needed functions, declarations, and adjacent logic; avoid whole large files/directories unless required.
- Do not repeatedly reread unchanged code or load directories "for context".
- Do not load full `graphify-out/graph.json`, `graph.html`, huge repo maps, DB dumps, diffs, or build logs.
- By default avoid broad exploration of `deps/`, build artifacts, and all of `src/server/scripts/`; open only relevant parts when required.
- Do not ignore relevant tests or SQL migrations merely to save tokens.
- Do not rebuild indexes/graphs after every edit. Update them only when stale data blocks the task.
- Do not start paid LLM indexing or full-repository scans without separate approval.
- Stop investigating once enough evidence exists to implement safely.
- Correctness outranks token savings: recover exact errors, source bodies, or diff context whenever needed.
- For long work, compact context only when needed; preserve the goal, constraints, changed files, verification results, and next step. Start unrelated major tasks in a clean context.

## BOT_BOT rules

These rules apply to bot interaction systems.

- BOT_BOT interactions may **start and continue only while at least one eligible real human observer is nearby**; a human merely being online elsewhere is insufficient.
- The observer must be a real human, not a playerbot, and must satisfy the module's map/instance/phase/distance/visibility rules.
- Observer presence permits an otherwise valid interaction; it does not trigger one.
- If the required common observer is lost, stop new module-owned actions and cancel/clean up at the correct safe boundary.
- Already-started indivisible core operations may finish safely before the scene stops.
- Bots interact through real game actions; no artificial BOT_BOT chat, textual emotes, or LLM dialogue.
- Communication with a real human player remains allowed; an observer does not turn BOT_BOT into BOT_PLAYER.
- Normal PlayerbotAI and unrelated background/world systems must continue without observers.

## Database and live server

- Use read-only DB access for investigation; never disable `READ_ONLY` on your own.
- Before SQL, verify the actual table, schema, and current data; never invent custom-module table names.
- You may prepare migrations, but apply DB changes only with explicit permission.
- SOAP commands, reloads, restarts, character changes, and other live-state mutations require explicit permission.
- SQL read-only mode does **not** protect against SOAP mutations.
- Do not stop the server or replace live binaries/configs merely to verify a build.

## Test-first development

For behavior changes and bug fixes, use test-first development by default:

1. Identify the behavior/regression to verify.
2. Write or extend the smallest relevant automated test **before** production implementation.
3. Run it and confirm it fails for the expected reason.
4. Implement the minimum production change required to pass.
5. Run the focused test again.
6. Run relevant surrounding/regression tests.
7. Build the affected target and perform runtime verification when gameplay behavior is involved.
8. Review the final diff.

If no relevant test exists, first inspect the project's existing test/integration infrastructure.

- If the behavior can reasonably be covered by existing infrastructure, add the test there.
- If full gameplay behavior cannot reasonably be automated, define a deterministic runtime/integration verification before implementation and add the closest practical automated coverage for testable policy/pure logic.
- Do not invent a new unrelated test framework solely for one task without explicit approval.
- Do not report a test as PASS merely because a test file exists; it must actually execute successfully.
- Do not weaken assertions, disable/delete failing tests, or write tests that merely mirror implementation.
- Compilation alone is not a substitute for behavior verification.

Documentation-only, generated-file-only, and tooling-configuration-only changes do not require artificial tests.

## Build workflow

- Preserve the existing build workflow. On the first necessary build, inspect the actual generator/toolchain/configuration from `CMakeCache.txt`, presets, or scripts.
- Do not change compiler/generator or delete `build/` just to satisfy clangd/ccache.
- Prefer incremental builds of affected targets while accounting for final worldserver linking when required.
- Save full build output to a log and inspect only relevant diagnostic blocks; preserve the real build exit code when filtering/redirecting output.
- Fix the first/root compiler or linker error before chasing downstream failures.
- Do not hide warnings caused by the current change.
- Do not "fix" later unfinished phases merely to make the current phase compile; prefer correct feature gating and the smallest scope-preserving build fix.

## Definition of Done

A task is not complete merely because code was written or compiled.

Before completion:

- review the final `git diff` for unrelated changes;
- build the affected target(s);
- run the new/changed focused tests plus relevant surrounding regression tests where applicable;
- verify error paths, invalid/null state, cleanup, cancellation, and rollback where applicable;
- for gameplay changes, state whether runtime behavior was actually tested;
- classify unverified criteria honestly;
- explicitly list anything not verified.

Never claim a bug is fixed or a phase is complete if only compilation was confirmed.

## Root-cause debugging

- Find and fix the root cause rather than masking symptoms.
- Do not add retries, delays, extra guards, disabled checks, commented-out functionality, or unrelated changes without evidence that they address the cause.
- Reproduce the issue or obtain observable evidence where practical.
- Reject hypotheses not supported by tools/source/runtime evidence.
- After a fix, summarize briefly: **cause → fix → verification**.

## Performance and hot paths

AzerothCore is a long-running real-time server. Be especially careful in update/tick loops, `UpdateAI`, Player/Unit/Creature, combat, movement, PlayerBots, and loops over many players/bots/objects.

Avoid without clear need:

- DB queries inside frequent update loops;
- full scans of large containers every tick;
- avoidable O(n²) behavior at scale;
- repeated computation of stable data;
- frequent heap allocations in hot paths;
- per-tick noisy logging;
- broad/global locking.

Before adding a periodic module tick/update, check whether an existing scheduler/event mechanism can be reused. Prefer event-driven logic or targeted indexes over global scans. Do not prematurely optimize, but call out meaningful complexity/frequency changes.

## Lifetime, ownership, and concurrency

Explicitly consider object lifetime for raw pointers, `ObjectGuid` lookups, Player/Creature/Unit references, logout/despawn/map changes, events/tasks, async DB callbacks, lambda captures, and shared state.

- Do not retain world-object pointers longer than their lifetime is guaranteed.
- Prefer reacquiring objects by `ObjectGuid` when lifetime across callbacks/events is uncertain.
- Check cleanup/cancellation when owners disappear or sessions/maps change.
- Do not add mutexes/atomics "just in case"; first determine which threads actually access the data.

## Compatibility

Preserve existing module/config behavior unless a breaking change is explicitly required.

Without need, do not rename config keys, change config semantics, alter public module APIs, modify DB schema, change DB-persisted enum values, or change established commands/data formats. If a breaking change is required, identify it clearly and include migration steps.

## Logging and diagnostics

- Add logs for diagnosis, not noise: what happened, to which entity/bot, and why a decision was accepted/rejected.
- Avoid per-tick spam and use existing AzerothCore/module log categories where possible.
- Remove temporary debug spam unless it has lasting diagnostic value.
- Never log credentials, tokens, or sensitive data.

## Final verification

After code changes:

1. run the focused test(s) written/updated for the task, if applicable;
2. run relevant regression tests;
3. build the affected target(s);
4. perform permitted runtime/gameplay checks when applicable;
5. inspect `git diff` and confirm no unrelated changes.

Report automated tests, build status, and runtime verification separately. Successful compilation alone does not prove gameplay behavior is correct.

## Response style

- Reply in Russian, briefly, using complete sentences.
- Report: what changed, what was verified, and what remains unverified.
- Do not narrate obvious tool/shell operations or repeat large tool outputs.
- Never claim a tool works, a test passed, a phase is complete, or a bug is fixed without corresponding verification.
