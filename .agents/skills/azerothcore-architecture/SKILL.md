---
name: azerothcore-architecture
description: >
  Analyze AzerothCore architecture and integration points without implementation.
---

# AzerothCore Architecture Analysis

Read `PROJECT.md` first.

Goal: answer the architectural question with the minimum investigation needed.

## Investigation

Use Graphify first for:
- subsystem relationships;
- lifecycle relationships;
- candidate integration points;
- comparable existing modules.

Prefer:
`graphify query`
before `path` or `explain`.

Do not exhaustively map the repository.

For one architecture decision:
- maximum 4 Graphify operations;
- maximum 3 targeted source reads.

Use source navigation only when a specific unresolved fact can materially change
the architectural decision.

Do not inspect implementation details that do not affect the decision.

Do not audit an existing module unless the user explicitly asks for an implementation review.

## Evidence

Separate:

- repository facts;
- architectural inference;
- recommendation.

Graphify relationships are orientation evidence.
Verify only critical runtime/lifecycle semantics in source.

## Jev

Gather evidence first.

Use Jev once when choosing between multiple genuinely valid designs.

Do not use Jev for repository facts.

Do not continue investigation after the decision unless Jev exposes a concrete unresolved blocker.

## Scope

For architecture-only tasks:

- do not edit files;
- do not write code;
- do not build;
- do not run tests;
- do not redesign unrelated systems.

## Finish condition

Stop when you have enough evidence to provide:

- relevant Graphify findings;
- Jev result when applicable;
- recommended architecture;
- main risks.

Do not continue searching merely to strengthen confidence.