---
name: plan-phase
description: Convert an AzerothCore PRD into small, verifiable implementation phases. Use when a completed PRD exists and an implementation plan is needed for AzerothCore WotLK 3.3.5a.
---

# Plan generation

Read the PRD from:

$ARGUMENTS

Save the result as:

`plan/plan-<slug>.md`

where `<slug>` is the PRD filename without path, extension, or the `prd-` prefix.

Example:

`docs/prd-bot-group-interactions.md`
→
`plan/plan-bot-group-interactions.md`

Do not change the existing English kebab-case slug.

Create the `plan` directory if it does not exist.

# Project context

This project is a customized AzerothCore WotLK 3.3.5a server.

Relevant implementation areas may include:

- `modules/**`
- `src/server/game/**`
- `src/server/shared/**`
- `src/server/database/**`
- configuration
- world/characters/auth databases
- runtime worldserver behavior

Prefer module-level implementation over AzerothCore core modifications when practical.

Do not assume a core change is necessary until existing module hooks/APIs have been checked.

# Investigation rules

Before planning implementation details, identify the relevant existing architecture.

Use the narrowest suitable source:

- AzerothMCP → DB, SmartAI, creatures, quests, conditions, runtime/server data
- Graphify → architecture and cross-module relationships
- clangd → exact C++ definitions, references, callers and inheritance
- Atlas → orientation only when the subsystem is unfamiliar
- ast-grep → repeated structural patterns
- rg → exact strings/config keys/log text

Do not plan broad repository exploration.

If an important implementation assumption cannot be verified, mark it as an open question rather than inventing architecture.

# Plan structure

# Plan: {plan filename}

**PRD:** $ARGUMENTS
**Date:** {current date}

## Scope

Short summary of what is being implemented.

## Existing architecture

Only include findings necessary for the plan:

- relevant modules/classes
- existing hooks/managers/APIs
- DB/config dependencies
- important integration points

Keep this section concise.

## Implementation phases

### Phase 1: {name}

**Goal:** Observable working result delivered by this phase.

**Touches:**
- module/core:
- database:
- config:
- runtime:

Only include categories that actually apply.

**Tasks:**
- [ ] Task
- [ ] Task
- [ ] Task

Maximum 5 tasks.

**Verification:**
- build:
- automated tests:
- runtime/gameplay:
- DB/log verification:

Only include applicable checks.

**Done when:**
A concrete, observable result exists.

Examples:

- worldserver builds successfully
- module loads without errors
- config option changes the expected behavior
- a real player action produces the expected game state
- playerbot performs the expected action
- BOT_BOT interaction follows the PRD rules
- expected DB state can be verified
- relevant automated tests pass

### Phase 2: {name}

...

# Phase design rules

- Phase 1 must be the smallest end-to-end Tracer Bullet that proves the implementation path.
- Every phase must leave the project buildable and usable.
- Every phase must have its own verification criteria.
- Later phases may depend on earlier phases, but each phase must be independently verifiable.
- Maximum 5 implementation tasks per phase.
- Prefer vertical behavior slices over arbitrary file/layer splits.
- Do not create separate phases merely because code touches different files.
- Do not split "backend" and "frontend"; AzerothCore is primarily server-side.
- Database/config changes belong in the phase that needs them unless they form a meaningful independently verifiable milestone.

# Testing and verification

Plan verification before implementation.

Use automated tests when suitable existing test infrastructure exists.

Do not invent a unit-test framework solely because the PRD needs verification.

For behavior without practical automated coverage, define a deterministic runtime test.

A phase may be verified by a combination of:

- targeted build
- existing unit/integration tests
- runtime worldserver scenario
- SOAP command
- AzerothMCP read-only inspection
- DB state verification
- expected logs
- in-game behavior

Compilation alone is not sufficient verification for gameplay behavior.

# AzerothCore-specific checks

When relevant, explicitly consider:

## Lifetime and state

- Player/Creature/Unit logout or despawn
- map changes
- ObjectGuid vs stored pointers
- delayed tasks/events
- group changes
- bot login/logout

## Performance

For code executed frequently or across many bots/players, check:

- tick/update frequency
- repeated world scans
- O(n²) loops
- DB queries in hot paths
- unnecessary allocations
- excessive logging

Do not add optimization tasks unless the PRD implementation creates a plausible performance concern.

## Compatibility

Preserve existing behavior unless the PRD explicitly changes it.

Pay attention to:

- module APIs
- config keys
- DB schema/data
- PlayerBots behavior
- existing server hooks
- saved/persistent values

## BOT_BOT behavior

If the PRD affects bot-to-bot interactions:

- interactions may start and continue only while a real human observer is nearby;
- a human merely being online is insufficient;
- bots must use real game actions rather than artificial bot-to-bot chat;
- interaction with a real player may use normal player-facing communication.

# Core modification rule

If a phase proposes changing AzerothCore core:

1. identify why module hooks/extensions are insufficient;
2. name the exact core integration point;
3. keep the change minimal;
4. include regression verification.

Do not modify core merely because it is easier.

# Database rules

If DB changes are required:

- identify the affected database: world / characters / auth;
- distinguish schema changes from data changes;
- prefer normal AzerothCore/module migration mechanisms;
- define how the change is verified;
- include rollback/migration considerations for destructive changes.

Do not add DB changes that are not required by the PRD.

# Rules

- Read the PRD completely.
- Cover every PRD acceptance criterion.
- Do not add user-visible features that are absent from the PRD.
- Engineering tasks required to implement, build, migrate or verify the requested behavior are allowed.
- Avoid unrelated refactoring.
- Reuse existing AzerothCore/PlayerBots infrastructure where practical.
- Keep the plan implementation-oriented and concise.
- Do not paste large source snippets into the plan.
- Do not include speculative architecture as fact.
- If the PRD contains a blocking ambiguity, ask for clarification before creating the final plan.