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

`/implement-phase plan/plan-bot-group-interactions.md 2`

# Input

From `$ARGUMENTS`, determine:

1. plan file path;
2. phase number.

Read:

- the requested phase;
- its goal;
- tasks;
- verification criteria;
- relevant preceding phase context only when required.

Do not load the whole repository for context.

If the requested phase does not exist, stop and report it.

If a prerequisite phase is clearly incomplete and blocks this phase, report the blocker instead of implementing around it.

# Scope

Implement ONLY the requested phase.

Do not:

- implement later phases;
- add unrelated features;
- perform unrelated refactoring;
- "prepare" future phases unless required by the current phase;
- expand the phase scope because another improvement seems useful.

Small engineering work required to complete or verify the requested phase is allowed.

# Subagents

For complex phases with independent investigation workstreams, use 2-3 focused
subagents.

When spawning investigation subagents, prefer the project agent:

`azeroth-researcher`

This agent is configured to use:

`claude-sonnet-5[1m]`

Do not substitute a cheaper/different model for AzerothCore investigation unless
the user explicitly requests it.

Subagents should:
- investigate one narrowly defined workstream;
- return concise evidence and relevant symbols/files;
- avoid large logs/source dumps;
- normally avoid final implementation.

The main agent should:
1. collect findings;
2. resolve conflicts;
3. determine the minimum implementation surface;
4. perform final integration and edits;
5. build and verify.

Do not use subagents for simple symbol lookups, trivial edits, or ordinary compile
errors.

Do not allow multiple subagents to edit overlapping files concurrently.

# Before editing

Confirm the current repository state.

Check:

- `git status`;
- relevant existing user changes;
- current phase requirements.

Never overwrite or discard unrelated user changes.

Determine the smallest implementation surface before editing.

# Investigation

Investigate only as much as needed to implement the phase correctly.

Follow the project's tool policy from `CLAUDE.md`.

Typical choices:

- AzerothMCP → DB/game data/runtime
- Graphify → architecture and dependency relationships
- clangd → exact C++ definitions/references/callers
- Atlas → initial orientation when the subsystem is unfamiliar
- ast-grep → structural patterns
- rg → exact strings/config/log text

Prefer precise queries over broad repository reading.

Do not use every tool automatically.

Once enough evidence exists to implement safely, stop investigating and implement.

# Architecture

Reuse existing AzerothCore and module mechanisms where practical.

Prefer module-level changes over AzerothCore core modifications.

Before modifying core, verify that an existing hook/module extension point cannot reasonably satisfy the phase.

If a core change is required:

- keep it minimal;
- preserve existing behavior;
- explain why the module layer was insufficient.

# Implementation

Implement the phase tasks with the minimum necessary changes.

Keep behavior focused on the plan.

While editing C++ code, pay attention when relevant to:

- object lifetime;
- `ObjectGuid` vs stored world-object pointers;
- logout/despawn;
- map/instance changes;
- group changes;
- delayed tasks/events;
- concurrency;
- hot update paths;
- repeated scans;
- DB queries in frequent code paths.

Do not introduce speculative abstractions.

Do not rewrite working code solely for style.

# Database and configuration

Only make DB/config changes explicitly required by the phase.

For DB work:

- identify `world`, `characters`, or `auth`;
- use normal AzerothCore/module migration mechanisms;
- avoid destructive operations unless explicitly required.

Do not use production/runtime DB data as a substitute for migrations.

For configuration:

- preserve existing keys and defaults unless the phase explicitly changes them;
- do not rename unrelated options.

# BOT_BOT invariants

When the phase affects BOT_BOT behavior, preserve the project invariants from `CLAUDE.md`.

In particular:

- new BOT_BOT interactions require a nearby real-player observer;
- active BOT_BOT interactions continue only while the required observer remains nearby;
- a human merely being online is insufficient;
- bots use real game actions rather than artificial bot-to-bot conversation.

# Build

After implementation, build the narrowest meaningful target first.

Use the existing build configuration.

Do not:

- replace the current compiler;
- change the main CMake generator;
- delete the build directory;
- clear build caches without a demonstrated reason.

If compilation fails:

1. inspect the first meaningful root error;
2. fix it;
3. rebuild;
4. only then inspect remaining errors.

Do not analyze large cascades of downstream errors before the root error.

# Verification

Verify against the phase's own verification and "Done when" criteria.

Use the appropriate combination of:

- targeted build;
- automated tests;
- runtime worldserver test;
- AzerothMCP read-only inspection;
- SOAP;
- DB state inspection;
- logs;
- in-game behavior.

Compilation alone does not prove gameplay behavior.

For every verification criterion, classify it as:

- PASS
- FAIL
- NOT VERIFIED

Never infer PASS without evidence.

If runtime verification cannot be performed, mark it `NOT VERIFIED`.

# Review

Before declaring the phase complete:

1. inspect `git diff`;
2. verify only intended files changed;
3. check for accidental debug code;
4. check for temporary logging;
5. check for unrelated refactoring;
6. confirm later phases were not implemented.

If the phase introduced a plausible regression risk, perform a focused regression check.

# Definition of Done

The phase is complete only when:

- all required phase tasks are implemented;
- the relevant target builds;
- planned automated tests pass where applicable;
- runtime/gameplay verification is performed where possible;
- acceptance/verification results are reported honestly;
- no unrelated user changes were overwritten;
- final diff is reviewed.

# Output

Keep the final report concise.

Use:

## Phase {number}: {name}

**Status:** COMPLETE / PARTIAL / BLOCKED

**Implemented**
- ...
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
- mention its number/name only;
- do NOT implement it.

Do not paste large logs or large source-code blocks.

# Rules

- Implement exactly one phase.
- Do not continue into the next phase automatically.
- Do not invent requirements absent from the PRD/plan.
- Do not silently weaken verification criteria.
- Do not claim runtime behavior was verified when only compilation succeeded.
- Prefer root-cause fixes over symptom suppression.
- Correctness takes priority over token savings.
- Stop when the requested phase is complete.