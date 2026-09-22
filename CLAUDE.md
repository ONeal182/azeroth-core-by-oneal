# AzerothCore Local-Model Development Rules

## Project

- Customized AzerothCore WotLK 3.3.5a with PlayerBots and custom modules.
- Work from the `azerothcore-wotlk` repository root and prefer relative paths.
- Scope includes `src/` and all of `modules/`.
- Respect the current Windows/WSL toolchain; do not switch paths, generators, compilers, or environments without verifying compatibility.

## Core behavior

- Make the smallest change that solves the requested task.
- Reuse existing AzerothCore/module mechanisms before creating new managers, helpers, schedulers, or parallel systems.
- Prefer module-level changes; modify core only when reasonably necessary.
- Preserve existing/user changes. Check `git status` before significant work.
- Never commit/push, `git reset --hard`, `git clean -fd`, delete major directories, or make broad rewrites unless explicitly requested.
- Do not change MCP, hooks, permissions, model/API routing, or optimization tooling during ordinary development.
- Never expose secrets.

## Local-model discipline

This session uses a local model. Minimize wandering, repeated searches, duplicated reasoning, and unnecessary tool calls.

### Hard investigation budget

For small tasks expected to touch 1–3 files:

- No subagents unless the user explicitly requests one in the current message.
- Maximum 3 broad searches.
- Maximum 10 search/read operations before the first edit.
- After a likely file/symbol is identified, all further searches must be path-scoped.
- Do not repeat equivalent searches with guessed names.
- Do not keep looking for a "better" API after a valid existing mechanism is found.
- If the budget is exhausted, summarize the evidence, choose the most supported implementation, make the smallest patch, and let build/tests validate it.

For medium tasks:

- Start narrow and expand only when evidence is insufficient.
- Prefer one investigation path at a time.
- Stop investigating as soon as the hook/entry point, relevant guard/condition, and existing mechanism/API are known.

### Decision checkpoint

After 5 investigation operations, before searching again, determine:

1. What exact fact is still unknown?
2. Is that fact required to implement safely?
3. Has an existing project mechanism already been found?
4. Can build/test feedback resolve the uncertainty faster than another search?

If nothing implementation-blocking remains, edit now.

### Never search these by default

Do not search generated/index/cache/build artifacts unless explicitly required:

- `graphify-out*`
- `build*`
- `.git/`
- `cache/`
- `*.backup*`
- generated logs
- dependency/vendor trees

Do not load full `graphify-out/graph.json`, `graph.html`, huge repo maps, DB dumps, or full build logs.

## Tool order

Use the most precise tool. This is guidance, not a mandatory chain.

### C++ navigation

1. **Graphify** — architecture, subsystem relationships, candidate files/classes.
2. **clangd MCP** — exact definitions, references, implementations, inheritance, call hierarchy, diagnostics.
3. **Read** — only the relevant function/declaration and nearby logic.
4. **rg/Grep** — exact strings, usage examples, config keys, log text.
5. **ast-grep** — structural patterns/refactors when appropriate.

Once Graphify identifies candidate files and clangd/source confirms the exact symbol, stop using Graphify for that question.

Do not use repository-wide grep to rediscover relationships already established by Graphify/clangd.

Do not invent likely API names such as `SendAdminMessage`. Search for the required behavior or existing usage instead.

### Other tools

- **AzerothMCP:** DB/schema, NPCs, items, quests, SmartAI, conditions, waypoints, spells, runtime/data lookups. Prefer specialized tools; use narrow SQL only if needed.
- **Atlas CLI:** only for first-pass orientation in genuinely unfamiliar code. Keep scope focused and token budget small.
- **Caveman:** compact output is fine for orientation; recover exact source/errors when correctness depends on omitted detail.
- **ccache:** preserve existing working integration; do not clear it.

If a tool is unavailable or stale, fall back to targeted source reads/search. Do not repair unrelated tooling during a coding task.

## Subagents

Do not use the Agent tool, background agents, or subagents unless the user explicitly requests them in the current message.

This applies even when parallel investigation seems useful.

Perform normal repository investigation in the main agent with Graphify, clangd, Read, Grep/rg, AzerothMCP, and Bash.

## Editing rule

Before the first edit, identify only what is necessary:

- correct hook/entry point;
- correct existing API/mechanism;
- required guard/exclusion conditions;
- affected file(s).

Once these are known, stop exploring and implement.

For simple glue changes, prefer:
`find hook -> find existing behavior/API -> patch -> build/test`

Do not narrate or restate the plan repeatedly.

## BOT_BOT rules

For bot interaction systems:

- BOT_BOT interactions may start and continue only while at least one eligible real human observer is nearby.
- A human merely online elsewhere is insufficient.
- The observer must be a real human, not a playerbot, and satisfy map/instance/phase/distance/visibility requirements.
- Observer presence permits an otherwise valid interaction; it does not trigger one.
- If the common observer is lost, stop new module-owned actions and cancel/clean up at the correct safe boundary.
- Already-started indivisible core operations may finish safely.
- BOT_BOT interactions use real game actions only; no artificial bot-bot chat, textual emotes, or LLM dialogue.
- Communication with real human players remains allowed.
- Normal PlayerbotAI and unrelated world/background systems must continue without observers.

## Database and live server

- Use read-only DB access for investigation.
- Verify real table/schema/data before SQL; do not invent table names.
- Prepare migrations if needed, but apply DB changes only with explicit permission.
- SOAP commands, reloads, restarts, character changes, and other live-state mutations require explicit permission.
- Do not stop the server or replace live binaries/configs merely to verify a build.

## Tests and verification

For behavior changes and bug fixes:

1. Identify the behavior/regression to verify.
2. Use the smallest relevant existing test if available.
3. Add/extend a focused test when practical.
4. Implement the minimum production change.
5. Run focused tests.
6. Build the affected target.
7. Perform permitted runtime verification for gameplay behavior.
8. Review `git diff`.

For trivial glue changes around existing hooks/APIs, do not spend large investigation effort creating new test infrastructure. If no focused test location is immediately available, make the minimal change, compile it, and provide a deterministic runtime verification procedure.

Never weaken assertions or disable/delete failing tests just to pass.

## Build workflow

- Preserve the existing build workflow.
- Inspect current generator/toolchain/configuration before the first necessary build.
- Prefer incremental builds of affected targets.
- Save full build output to a log; inspect only relevant diagnostics while preserving the real exit code.
- Fix the first/root compiler or linker error before downstream errors.
- Do not hide warnings caused by the current change.
- Do not delete `build/` or switch toolchains just to make clangd/ccache happy.

## Root-cause debugging

- Fix root causes, not symptoms.
- Do not add retries, delays, broad guards, disabled checks, or unrelated changes without evidence.
- Reproduce or obtain observable evidence when practical.
- Reject unsupported hypotheses.
- After a fix, summarize briefly: cause -> fix -> verification.

## Performance / lifetime

AzerothCore is a long-running real-time server.

Be careful in update loops, combat, movement, Player/Unit/Creature, PlayerBots, and loops over many objects.

Avoid without clear need:

- DB queries in frequent loops;
- global/full scans every tick;
- avoidable O(n²);
- repeated stable-data computation;
- frequent allocations/log spam;
- broad/global locking.

For raw pointers, ObjectGuid lookups, async callbacks, events/tasks, logout/despawn/map changes:

- do not retain world-object pointers beyond guaranteed lifetime;
- reacquire by `ObjectGuid` when lifetime is uncertain;
- verify cleanup/cancellation when owners disappear.

## Compatibility

Preserve existing public APIs, config keys/semantics, DB schema/enums, commands, and data formats unless the task explicitly requires a breaking change.

## Definition of Done

Before saying a task is complete:

- inspect final `git diff`;
- verify no unrelated changes;
- run focused tests when applicable;
- build affected target(s);
- report runtime verification separately;
- state anything not verified.

Compilation alone does not prove gameplay behavior is correct.

## Response style

- Reply in Russian, briefly, with complete sentences.
- Report only: what changed, what was verified, what remains unverified.
- Do not narrate obvious tool/shell operations.
- Do not repeat large tool outputs.
- Never claim a tool/test/build/runtime result without actual verification.
