# AzerothCore Project Rules

## Project

- Customized AzerothCore WotLK 3.3.5a with PlayerBots and custom modules.
- Work from the `azerothcore-wotlk` repository root and prefer relative paths.
- Scope includes `src/` and all of `modules/`.
- Respect the current Windows/WSL toolchain.
- Do not switch paths, generators, compilers, or environments without verifying compatibility.

## Workflow authority

Repository investigation, search strategy, tool budgets, Jev usage,
subagent policy, post-edit behavior, token discipline, and diff discipline
are defined only in:

`.agents/skills/azerothcore/SKILL.md`

Do not create a second search/tool workflow in this file.

For non-trivial AzerothCore coding tasks, follow that skill.

## Core behavior

- Make the smallest change that solves the requested task.
- Reuse existing AzerothCore/module mechanisms before creating new managers,
  helpers, schedulers, or parallel systems.
- Preserve existing/user changes.
- Do not make unrelated refactors.
- Never commit or push unless explicitly requested.
- Never run `git reset --hard`, `git clean -fd`, delete major directories,
  or perform broad rewrites unless explicitly requested.
- Do not change MCP, hooks, permissions, model/API routing,
  or optimization tooling during ordinary development.
- Never expose secrets.

## BOT_BOT rules

For bot interaction systems:

- BOT_BOT interactions may start and continue only while at least one eligible
  real human observer is nearby.
- A human merely online elsewhere is insufficient.
- The observer must be a real human, not a playerbot.
- The observer must satisfy map/instance/phase/distance/visibility requirements.
- Observer presence permits an otherwise valid interaction; it does not trigger one.
- If the common observer is lost, stop new module-owned actions and cancel/clean up
  at the correct safe boundary.
- Already-started indivisible core operations may finish safely.
- BOT_BOT interactions use real game actions only.
- Do not generate artificial bot-bot chat, textual emotes, or LLM dialogue.
- Communication with real human players remains allowed.
- Normal PlayerbotAI and unrelated world/background systems must continue
  without observers.

## Database and live server

- Use read-only DB access for investigation unless write access is explicitly requested.
- Verify the real table/schema/data before writing SQL.
- Do not invent table names.
- Prepare migrations when needed, but apply DB changes only with explicit permission.
- SOAP commands, reloads, restarts, character changes, and other live-state mutations
  require explicit permission.
- Do not stop the server or replace live binaries/configs merely to verify a change.

## Tests and verification

Follow the AzerothCore skill for when builds/tests are allowed.

When the user explicitly requests verification:
- use the smallest relevant existing test when possible;
- add a focused test only when practical and appropriate;
- build only the affected target when possible;
- preserve the existing toolchain/build configuration;
- report build, automated tests, and runtime verification separately.

Do not:
- weaken assertions;
- disable/delete failing tests;
- invent a new test framework for one small task;
- claim a test passed when it was not actually executed;
- treat compilation alone as proof of gameplay correctness.

## Build workflow

When a build is explicitly requested:

- preserve the existing build workflow;
- inspect the current generator/toolchain/configuration before changing it;
- prefer incremental builds of affected targets;
- do not rebuild unrelated targets;
- save large build output to a log;
- inspect only relevant diagnostics;
- preserve the real build exit code;
- fix the first/root compiler or linker error before downstream failures;
- do not hide warnings caused by the current change;
- do not delete `build/`;
- do not switch toolchains merely to satisfy clangd/ccache.

## Root-cause debugging

- Fix root causes rather than masking symptoms.
- Do not add retries, delays, broad guards, disabled checks,
  or unrelated changes without evidence.
- Reproduce the issue or obtain observable evidence when practical.
- Reject hypotheses not supported by source/tool/runtime evidence.
- After a fix, summarize briefly:

  `cause -> fix -> verification`

## Performance

AzerothCore is a long-running real-time server.

Be especially careful in:
- update/tick loops;
- combat;
- movement;
- Player/Unit/Creature paths;
- PlayerBots;
- loops over many players/bots/objects.

Avoid without clear need:
- DB queries in frequent update loops;
- global/full scans every tick;
- avoidable O(n²) behavior;
- repeated computation of stable data;
- frequent heap allocations in hot paths;
- per-tick log spam;
- broad/global locking.

Before adding periodic work, prefer an existing scheduler/event mechanism
when one already exists.

Do not prematurely optimize, but call out meaningful complexity/frequency changes.

## Lifetime and ownership

For raw pointers, `ObjectGuid` lookups, Player/Creature/Unit references,
events/tasks, async callbacks, logout/despawn, and map changes:

- do not retain world-object pointers beyond their guaranteed lifetime;
- prefer reacquiring objects by `ObjectGuid` when lifetime is uncertain;
- verify cleanup/cancellation when owners disappear;
- do not add mutexes/atomics without first determining actual thread access.

## Compatibility

Preserve existing behavior unless the task explicitly requires a breaking change.

Without explicit need, do not:
- rename config keys;
- change config semantics;
- alter public module APIs;
- modify DB schema;
- change DB-persisted enum values;
- change established commands/data formats.

If a breaking change is required, identify it clearly and include migration steps.

## Logging and diagnostics

- Add logs for useful diagnosis, not noise.
- Prefer existing AzerothCore/module log categories.
- Avoid per-tick spam.
- Remove temporary debug spam unless it has lasting diagnostic value.
- Never log credentials, API keys, tokens, or sensitive information.

## Definition of Done

Before saying a task is complete:

- ensure only requested files/behavior were changed;
- inspect only the scoped diff for files changed by the current task;
- perform build/tests/runtime verification only when explicitly requested
  or required by the current task;
- state clearly what was and was not verified.

Do not continue repository investigation after the requested patch is complete.

Never claim:
- a bug is fixed;
- a build succeeded;
- a test passed;
- runtime behavior was verified

without corresponding evidence.

## Response style

- Reply in Russian unless the user requests another language.
- Be brief and use complete sentences.
- Report only what changed, what was verified, and what remains unverified.
- Do not narrate obvious tool/shell operations.
- Do not repeat large tool outputs.