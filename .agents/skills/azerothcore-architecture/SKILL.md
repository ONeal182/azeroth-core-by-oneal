---
name: azerothcore-architecture

description: >
  Analyze AzerothCore architecture, integration points, subsystem boundaries,
  and design choices without implementing code.
---

# AzerothCore Architecture Workflow

Use this skill when the task is:

- architecture design;
- choosing integration points;
- comparing valid designs;
- planning a new subsystem;
- reviewing subsystem boundaries.

Do not use this workflow for normal small patches.

---

# Goal

Produce an architecture decision based on sufficient evidence.

The goal is not to understand the entire repository.

Find:

- where responsibility belongs;
- which existing systems should be reused;
- what the integration boundary should be;
- the main risks.

Stop when the decision is supported.

---

# Rules

## No implementation

Architecture tasks:

- do not write code;
- do not edit files;
- do not create migrations;
- do not build;
- do not run tests;
- do not change runtime state.

---

# Investigation workflow

## Step 1 — Understand the question

Identify:

1. What system is being added or changed?
2. Which existing subsystems are involved?
3. What architectural decision must be made?

Do not investigate unrelated areas.

---

# Step 2 — Graphify first

Use Graphify for:

- subsystem relationships;
- dependency boundaries;
- existing extension points;
- similar modules;
- lifecycle relationships.

Good Graphify questions:

- "How does WorldScript connect to event systems?"
- "What owns creature lifecycle?"
- "How do Playerbots choose travel targets?"

Avoid using Graphify for:

- exact constants;
- finding one function;
- replacing normal source lookup.

---

# Graphify stopping rule

Graphify is an orientation tool.

Stop when you know:

- the main integration boundary;
- the involved subsystem owners;
- the relevant lifecycle flow.

Do not:

- map the entire repository;
- explore every related class;
- continue searching for confidence.

---

## Evidence threshold

Architecture decisions usually require only:

- one ownership flow;
- one lifecycle flow;
- one integration boundary.

When these are identified, make the recommendation.

Do not continue investigation to collect supporting examples.

Sufficient evidence is enough.

---

# Step 3 — Source verification

Use source reading only for unresolved details.

Verify only:

- lifecycle behavior;
- API ownership;
- important data flow;
- existing contracts.

Prefer:

one definition + one usage

over broad exploration.

---

## Source reading depth

Architecture tasks are not implementation reviews.

Do not read large `.cpp` files.

Prefer:

- headers;
- interfaces;
- class responsibilities;
- public methods.

Read implementation `.cpp` only when:

- ownership is unclear;
- lifecycle behavior cannot be determined otherwise;
- the implementation itself is the architecture under review.

Do not read more than ~100 lines of one implementation file unless required.

Do not reconstruct implementation history.

Avoid reading:

- large managers;
- complete event classes;
- unrelated AI behavior;
- every caller of a discovered API.

Only inspect enough code to determine ownership and boundaries.

---

# Architecture investigation budget

Before making a recommendation:

Maximum:

Graphify:

- 3 focused queries.

Source:

- 5 targeted file/function reads.

Exceed only when:

- two subsystems have conflicting ownership;
- lifecycle behavior remains unknown;
- the decision cannot be made otherwise.

This is a ceiling, not a target.

If the architecture decision is already clear:

stop earlier.

---

# Existing implementation vs recommendation

Existing code shows current behavior.

It does not automatically represent the best architecture.

Separate:

## Facts

What currently exists.

## Constraints

What must be preserved.

## Recommendation

What architecture should be used.

Do not choose a design only because current code already follows it.

---

# Design comparison

When comparing designs:

Evaluate:

- ownership;
- lifecycle;
- data flow;
- extension ability;
- cleanup;
- failure cases;
- future compatibility.

Avoid choosing based only on:

- fewer files;
- less code;
- current implementation similarity.

---

# Playerbots

When architecture involves Playerbots:

Preserve:

- PlayerbotAI ownership;
- existing travel/combat systems;
- bot lifecycle;
- BOT_BOT rules.

Prefer:

- world systems expose state/events;
- Playerbots decide their own actions through normal mechanisms.

Integration should normally cross through:

- public state;
- existing ScriptMgr hooks;
- existing AI decision points.

Avoid:

- direct bot control from unrelated modules;
- new bot managers;
- LLM-driven behavior.

---

# World objects lifecycle

For systems involving:

- Creature;
- GameObject;
- Map;
- Instance;

consider:

- ownership;
- creation;
- destruction;
- map unload;
- stale references.

Prefer stable identifiers such as ObjectGuid over long-lived object pointers.

---

# Database architecture

For database-related design:

Verify:

- database ownership;
- existing migration patterns;
- schema contracts.

Do not design tables before understanding existing patterns.

---

# Tool usage

## Graphify

Use for:

- relationships;
- architecture;
- impact analysis.

## Graphify query discipline

Prefer a small number of focused queries.

Typical architecture investigation:

1. subsystem boundary;
2. lifecycle/data flow;
3. integration point.

Avoid repeating queries with different synonyms after relevant nodes are found.

---

## clangd/source

Use for:

- definitions;
- references;
- lifecycle semantics;
- call paths.

---

## AzerothMCP

Use for:

- NPC IDs;
- spells;
- items;
- quests;
- maps;
- database-backed game data.

---

## Jev

Use only for genuine unresolved design choices.

Correct usage:
