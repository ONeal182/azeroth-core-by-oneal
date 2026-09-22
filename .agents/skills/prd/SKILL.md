---
name: prd
description: Create concise product requirements for an AzerothCore WotLK 3.3.5a feature before implementation. Defines behavior, scope, constraints, edge cases, and verifiable acceptance criteria without prescribing implementation.
---

# PRD Generator

Create a PRD for:

$ARGUMENTS

Save it as:

`docs/prd-<slug>.md`

where `<slug>` is an English kebab-case feature name without punctuation.

Example:

`Bot group interactions`
→
`docs/prd-bot-group-interactions.md`

Create `docs/` if it does not exist.

# Project context

This is a customized AzerothCore WotLK 3.3.5a server.

Possible actors include:

- real player
- PlayerBot
- group/raid
- NPC/creature
- GM/server administrator
- worldserver/system

Use only actors relevant to the feature.

Existing project rules and invariants from `CLAUDE.md` remain authoritative.

If the feature affects BOT_BOT interactions, preserve the existing observer and real-game-action rules unless the requested feature explicitly changes them.

# Clarification rule

Before writing the PRD, identify only ambiguities that materially affect behavior or acceptance criteria.

Ask questions only when a blocking requirement cannot be determined.

Do not delay PRD creation for minor details that can safely remain unspecified.

Do not invent gameplay rules that were not requested.

# Document structure

# PRD: {feature name}

**Date:** {current date}

**Status:** Draft

## Goal

1-2 sentences describing:

- what capability is being added;
- why it is needed.

Do not describe implementation.

## Actors

List only actors involved in this feature.

Example:

- Real player
- PlayerBot
- Worldserver

## Scenarios

Describe observable behavior.

Format:

- `{actor} performs {action} -> {observable result}`

Examples:

- Real player enters a group with PlayerBots -> bots participate using normal group mechanics.
- Player moves outside the observer range -> no new BOT_BOT interaction starts.
- Server administrator disables the feature -> the behavior no longer occurs.

Do not mention classes, functions, files, or implementation details.

## In Scope

Concrete behavior included in this iteration.

- ...
- ...

## Out of Scope

Explicitly excluded behavior.

- ...
- ...

Do not add speculative future features only to fill this section.

## Behavioral Requirements

Describe rules the feature must satisfy.

Use precise statements such as:

- MUST
- MUST NOT
- SHOULD

Only include requirements relevant to the requested feature.

## Constraints and Invariants

List existing rules that the feature must preserve.

Possible examples when relevant:

- existing AzerothCore gameplay behavior must remain compatible;
- existing PlayerBots behavior outside this feature must not change;
- BOT_BOT interaction requires a nearby real-player observer;
- bots use actual game mechanics rather than artificial bot-to-bot chat;
- disabling the feature restores existing/default behavior.

Do not include implementation choices here.

## Configuration Requirements

Include this section only if the feature exposes configuration.

Describe:

- what behavior must be configurable;
- expected default behavior;
- valid behavioral boundaries.

Do NOT specify config variable names unless they are already part of the requested public interface.

If no configuration is required, omit this section.

## Data and Persistence Requirements

Include only if persistent state matters.

Describe WHAT must persist and under what conditions.

Examples:

- state survives worldserver restart;
- state is character-specific;
- temporary interaction state does not persist.

Do not specify SQL tables, columns, schemas, or migrations.

## Edge Cases

List meaningful behavioral edge cases.

Consider only where relevant:

- player logout
- bot logout
- despawn
- death/resurrection
- map/instance change
- group changes
- observer leaving
- server restart
- feature disabled
- invalid or missing target
- simultaneous interactions
- stale state

Do not invent edge cases unrelated to the feature.

## Acceptance Criteria

Every criterion must be independently observable and verifiable.

Use:

- [ ] Given {precondition}, when {action/event}, then {observable result}

Good examples:

- [ ] Given two eligible PlayerBots and a nearby real player observer, when the interaction conditions are met, the bots perform the expected real game action.
- [ ] Given an active BOT_BOT interaction, when the required real-player observer is no longer nearby, the interaction no longer continues.
- [ ] Given the feature is disabled, when the triggering conditions occur, no feature-specific behavior is observed.
- [ ] Given a bot logs out during the feature flow, no invalid/stale behavior remains after logout.

Possible observable results include:

- in-game state
- player/bot action
- group membership
- combat state
- inventory/state change
- persisted state
- expected server log
- runtime/server behavior

Compilation success is NOT a PRD acceptance criterion.

## Non-Goals

Optional.

Use only when needed to prevent a likely scope misunderstanding.

Do not duplicate `Out of Scope`.

# Rules

- Be concise and specific.
- Define WHAT and WHY, never HOW.
- Do not name implementation files/classes/functions unless the requested feature itself exposes them as part of its contract.
- Do not prescribe C++, SQL, hooks, managers, APIs, algorithms, or architecture.
- Do not perform implementation investigation for a normal PRD.
- Do not add features that were not requested.
- Preserve existing project invariants unless the requested feature explicitly changes them.
- Every acceptance criterion must describe externally observable or runtime-verifiable behavior.
- Avoid vague criteria such as "works correctly", "handles errors", or "is optimized".
- Do not require automated tests in the PRD; testing strategy belongs in `plan-phase`.
- If a blocking behavioral ambiguity remains, ask for clarification before writing the final PRD.