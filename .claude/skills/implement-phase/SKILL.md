---
name: implement-phase
description: Implement exactly one phase from an AzerothCore implementation plan, verify it, and stop before later phases.
---

# Implement Phase

Implement exactly one phase from an existing implementation plan.

Arguments:

$ARGUMENTS

Expected usage:

`/implement-phase plan/plan-<feature>.md <phase-number>`

Example:

`/implement-phase plan/plan-playerbot-interactions.md 6`

## Input

From `$ARGUMENTS`, determine:

1. plan file path;
2. phase number.

Read:

- the requested phase;
- its goal;
- tasks;
- verification criteria;
- relevant cross-cutting invariants;
- only the preceding phase context required to understand prerequisites.

Do not load the whole repository for context.

Do not load the entire implementation plan into context unless required.

For the current phase:
- read only the phase section;
- read previous phases only for dependencies;
- do not analyze future phases.

If the requested phase does not exist, stop and report it.

If a prerequisite phase is clearly incomplete and blocks this phase, report the blocker instead of implementing around it.

## Scope

Implement **ONLY** the requested phase.

Do not:

- implement later phases;
- add unrelated features;
- perform unrelated refactoring;
- "prepare" future phases unless required by the current phase;
- expand scope because another improvement seems useful;
- disable/comment out working behavior from completed phases merely to make the build pass.

Small engineering work required to complete, compile, test, or verify the requested phase is allowed when it preserves existing behavior.

## Investigation strategy

Do **not** spawn subagents unless the user explicitly requests them.

Perform investigation in the main agent using the project's targeted tools.

Use the cheapest precise tool first:

- Graphify → architecture, subsystem relationships, dependencies, and impact analysis;
- clangd → exact C++ definitions, references, implementations, callers, inheritance, symbols, and diagnostics;
- AzerothMCP → database, SmartAI, game data, runtime state, and SOAP/read-only checks;
- Atlas → initial orientation only when the subsystem is genuinely unfamiliar;
- ast-grep → structural code patterns/refactors;
- `rg` → literal strings, config keys, file names, SQL names, and log text;
- targeted Read → only after narrowing the relevant file/symbol.

Do not mechanically use every tool.

Do not treat Graphify paths through generic primitives such as `_string`, `string`, `uint32`, `uint8`, or `int32` as meaningful architectural evidence; verify important C++ relationships with clangd/source.

Avoid broad repository exploration when a targeted tool can answer.

Stop investigating once enough evidence exists to implement safely.

Keep context small:

- avoid large source dumps;
- avoid huge grep results;
- avoid full build logs;
- do not reread unchanged files without reason;
- do not load raw Graphify JSON/HTML for ordinary work.

## AzerothMCP usage


Use AzerothMCP for game data and runtime information.

Prefer AzerothMCP over source search for:

- NPC entries;
- creature templates;
- item IDs;
- spell IDs;
- quests;
- achievements;
- maps;
- loot;
- SmartAI;
- database-backed game data;
- runtime state checks.

Do not search source code for static game data when AzerothMCP can provide the answer.

Use source code investigation when:
- implementing behavior;
- finding hooks;
- changing server logic;
- modifying modules.

## Before editing

Before implementing a phase:

- check existing feature documentation if it exists;
- treat it as the current implementation state;
- update it after successful completion.

Confirm the repository state.

Check:

- `git status`;
- relevant existing user changes;
- current phase requirements and cross-cutting invariants.

Never overwrite or discard unrelated user changes.

Determine the smallest implementation surface before editing.

For cross-cutting phases, create a concise coverage/lifecycle matrix when useful before changing code so missing integration points are explicit.

## Architecture

Reuse existing AzerothCore and module mechanisms where practical.

Prefer module-level changes over AzerothCore core modifications.

Before modifying core, verify that existing hooks/module extension points cannot reasonably satisfy the phase.

If a core change is required:

- keep it minimal;
- preserve existing behavior;
- explain why the module layer was insufficient.

Do not create parallel managers/schedulers/services when an existing subsystem can be extended safely.

## Architecture restraint

Do not redesign the architecture described in the plan.

Prefer:
- existing AzerothCore patterns;
- simple module APIs;
- direct phase-scoped implementations.

Do not introduce:
- generic frameworks;
- plugin systems;
- event buses;
- managers/services;
- abstractions for future phases

unless the current phase requires them.

## Test-first workflow

For executable behavior changes and bug fixes:

1. Identify the behavior/regression to verify.
2. Inspect the existing test/integration infrastructure.
3. Write or extend the smallest relevant automated test **before** production implementation when reasonably supported.
4. Run it and confirm RED for the expected reason.
5. Implement the minimum production change required to pass.
6. Run the focused test again and confirm GREEN.
7. Run relevant surrounding/regression tests.
8. Build and perform runtime verification when gameplay behavior is involved.

If no suitable automated test infrastructure exists:

- do not invent a new unrelated framework solely for this phase without explicit approval;
- isolate and test pure/policy logic where practical using existing infrastructure;
- define deterministic runtime/integration verification before implementation for the remaining behavior;
- mark runtime-only criteria `NOT VERIFIED` until actually executed.

A test file merely existing is not PASS.

Never weaken/delete/disable tests to make the phase appear complete.

## Implementation

Implement the phase tasks with the minimum necessary changes.

Keep behavior focused on the plan.

## Tracer bullet rule

For the first implementation phase of a new system:

Prefer a tracer bullet implementation.

Do not build all planned abstractions first.

Implement:

- one real trigger;
- one real reward path;
- one persistence path;
- one verification path.

Expand only after the tracer bullet works



While editing C++ code, consider when relevant:

- object lifetime;
- `ObjectGuid` vs stored world-object pointers;
- logout/despawn;
- map/instance/phase changes;
- group changes;
- delayed tasks/events;
- ownership/reservations;
- cancellation and safe transaction boundaries;
- concurrency;
- hot update paths;
- repeated scans;
- DB queries in frequent paths.

Do not introduce speculative abstractions.

Do not rewrite working code solely for style.

## Database and configuration

Only make DB/config changes explicitly required by the phase.

For DB work:

- identify `world`, `characters`, or `auth`;
- verify the actual schema first;
- use normal AzerothCore/module migration mechanisms;
- avoid destructive operations unless explicitly approved.

For module SQL:

- follow existing module migration structure;
- inspect a similar module before creating new SQL layout;
- do not invent naming conventions if an existing module pattern exists.

Do not use production/runtime DB data as a substitute for migrations.

For configuration:

- preserve existing keys/defaults unless the phase explicitly changes them;
- do not rename unrelated options.

## BOT_BOT invariants

When the phase affects BOT_BOT behavior, preserve the project invariants from `CLAUDE.md`.

In particular:

- BOT_BOT interactions may start and continue only with at least one eligible common real-human observer nearby;
- a human merely being online elsewhere is insufficient;
- observer presence is permission, not a trigger;
- observer eligibility must be revalidated at the lifecycle points required by the plan;
- observer loss stops new module-owned actions and cancels/cleans up at the appropriate safe boundary;
- already-started indivisible core operations may finish safely;
- bots use real game actions;
- BOT_BOT chat, textual emotes, and LLM dialogue remain forbidden;
- normal PlayerbotAI and unrelated background/world systems continue without observers.

## Build

After implementation, build the narrowest meaningful target first.

Use the existing build configuration.

Do not:

- replace the current compiler;
- change the main CMake generator;
- delete the build directory;
- clear build caches without a demonstrated reason;
- implement later phases merely to fix current build errors.

If compilation fails:

1. inspect the first meaningful root error;
2. classify it:
   - current-phase issue;
   - pre-existing dependency issue required to verify this phase;
   - unrelated later-phase issue;
3. fix current-phase issues;
4. for required pre-existing blockers, make only the smallest correct behavior-preserving fix;
5. for unrelated later-phase code, prefer correct existing feature/build gating rather than implementing that phase;
6. rebuild;
7. only then inspect remaining errors.

Do not hide failures by commenting out working functionality from completed phases.

## Verification

Verify against the phase's own tasks, verification criteria, and `Done when`.

Use the appropriate combination of:

- focused automated tests;
- relevant regression tests;
- targeted build/worldserver build;
- runtime worldserver scenario;
- AzerothMCP read-only inspection;
- SOAP when explicitly permitted;
- DB state inspection;
- logs;
- in-game behavior.

Compilation alone does not prove gameplay behavior.

For every verification criterion classify it as:

- `PASS`
- `FAIL`
- `NOT VERIFIED`

Only mark `PASS` when corresponding evidence actually exists.

Examples:

- test exists but was not executed → `NOT VERIFIED`;
- code path inspected only → not runtime PASS;
- worldserver compiles → build PASS only;
- gameplay scenario not run → `NOT VERIFIED`.

## Review

Before declaring the phase complete:

1. inspect `git diff`;
2. verify only intended files changed;
3. check for accidental debug code;
4. check for temporary/noisy logging;
5. check for commented-out or disabled existing functionality;
6. check for unrelated refactoring;
7. confirm later phases were not implemented;
8. perform a focused regression check when the change plausibly affects completed phases.

If compile fixes touched earlier/later phases, explicitly classify and justify each such change.

## Phase documentation

After completing a phase, update phase documentation.

Create or update:

`.agents/docs/features/<feature-name>/`

Structure:

- `overview.md` — current system architecture and purpose;
- `phase-status.md` — completed phases, current phase, remaining phases;
- `decisions.md` — important technical decisions and reasons;
- `api.md` — public APIs, hooks, commands, configs;
- `database.md` — created tables, fields, migrations.

Documentation rules:

- Document only what was actually implemented.
- Do not document future planned behavior as completed.
- Do not copy the entire PRD.
- Do not paste large code blocks.
- Prefer short factual descriptions.

After each completed phase:
- update the affected documentation;
- record changed files;
- record verification results;
- record known limitations/blockers.

Before starting a new phase:
- read only the relevant feature documentation;
- use it as the current implementation state;
- do not rediscover already documented architecture unless the code contradicts it.

## Definition of Done

The phase is `COMPLETE` only when:

- all required phase tasks are implemented;
- no required lifecycle/coverage item remains missing;
- relevant code compiles;
- focused automated tests pass where practical and supported;
- runtime/gameplay checks are executed where available/required, or honestly remain `NOT VERIFIED`;
- completed earlier-phase behavior was not disabled/regressed;
- no unrelated user changes were overwritten;
- the final diff is reviewed;
- verification is reported honestly.

Use `PARTIAL` when implementation exists but required verification, coverage, or blockers remain.

Use `BLOCKED` when a prerequisite/environment issue prevents meaningful progress.

## Output

Keep the final report concise.

Use:

### Phase {number}: {name}

**Status:** COMPLETE / PARTIAL / BLOCKED

**Implemented**
- ...

**Files changed**
- ...

**Verification**
- PASS — ...
- FAIL — ...
- NOT VERIFIED — ...

**Remaining**
- only blockers or unfinished items from THIS phase

**Next phase**
- mention number/name only;
- do NOT implement it.

For cross-cutting phases, include a concise lifecycle/coverage matrix when it materially supports verification.

Do not paste large logs or large source-code blocks.

## Rules

- Implement exactly one phase.
- Do not continue into the next phase automatically.
- Do not spawn subagents unless explicitly requested.
- Do not invent requirements absent from the PRD/plan.
- Do not silently weaken verification criteria.
- Do not claim tests passed if they were not executed.
- Do not claim runtime behavior was verified when only compilation succeeded.
- Do not disable completed functionality merely to obtain a successful build.
- Prefer root-cause fixes over symptom suppression.
- Correctness takes priority over token savings.
- Stop when the requested phase is complete or honestly PARTIAL/BLOCKED.
