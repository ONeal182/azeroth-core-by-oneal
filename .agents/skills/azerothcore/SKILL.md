---
name: azerothcore
description: >
  Use for coding, debugging, searching, reviewing, SQL, scripts, modules,
  playerbots, builds, tests, and e2e work in this AzerothCore repository.
---

# AzerothCore workflow

Goal: solve the requested task with the smallest correct change while reusing
existing AzerothCore architecture, hooks, APIs, and patterns.

## Search workflow

Choose the search strategy based on task size.

### Small-task fast path

Use this path when the user describes the task as small, minimal, simple,
focused, or preferably one-file.

Do not use Graphify for small tasks unless architecture or cross-subsystem
relationships are genuinely required.

Search exact symbols directly with `rg`.

Never run repository-wide searches with broad terms or large OR-patterns.

Bad:

`PlayerBot|IsBot|playerbots`

`IsPlayerbot|GetPlayerbotAI|IsBot|PLAYERBOT`

Prefer:
- one exact symbol at a time;
- a scoped directory;
- a file-type filter.

Example:

`rg -n "IsBot\(" src/server/game -g "*.cpp" -g "*.h"`

Find only the facts required to implement:
- the relevant hook/call site;
- the required public API/predicate;
- one existing usage when verification is useful.

Hard budget before the first edit:
- maximum 4 searches;
- maximum 2 source reads;
- maximum 6 search/read operations total.

A failed search or read counts toward the budget.

When a search returns one valid public API/predicate usage:
- treat it as sufficient evidence;
- do not search for additional examples;
- do not repeat the same concept with alternate regexes;
- do not investigate how it is internally populated unless correctness depends on it.

A valid public predicate plus one existing usage closes that research question.

Do not inspect how that predicate is implemented, populated, or assigned unless
the requested patch directly depends on those internals.

Do not trace:
- object construction;
- session creation;
- flag assignment;
- internal call chains

after a suitable public API has already been identified.

Do not search for a second implementation after one valid implementation is found.

Once the required hook/API/predicate is known, the next action MUST be an edit,
unless one additional fact is strictly required to write the patch correctly.

Do not perform another search merely to increase confidence.

If one genuine ambiguity remains after the budget:
- use Jev once if it can decide whether further investigation is justified;
- otherwise perform one additional targeted search.

Do not exceed the budget merely to increase confidence.

Target flow:

`focused rg -> relevant read -> patch`

### Broader codebase workflow

Use this workflow for medium/large tasks, architecture questions,
cross-subsystem changes, or when the small-task fast path is insufficient.

1. If `graphify-out/graph.json` exists, attempt:
   `graphify query "<question>"`

2. Do not glob/search Graphify files before trying the query.

3. If Graphify is unavailable or fails once:
   - fall back immediately to `rg`;
   - do not retry Graphify for the same question.

4. Use:
   `graphify path "<A>" "<B>"`
   only when relationships between components are actually relevant.

5. Use:
   `graphify explain "<concept>"`
   only for focused architectural concepts.

6. Use `rg` for:
   - exact symbols;
   - hook names;
   - API names;
   - concrete strings;
   - implementation searches;
   - cases where Graphify is insufficient.

7. Prefer `graphify-out/wiki/index.md` for broad navigation.

8. Read `graphify-out/GRAPH_REPORT.md` only for broad architecture work
   or when scoped Graphify queries are insufficient.

Search narrowly.

Do not repeat equivalent searches.

Do not reread unchanged code unless new information requires it.

Read only relevant ranges.

Do not read entire large files when a symbol or small range is sufficient.

When one clear existing usage is found, do not search for more examples unless
the first usage is ambiguous or unsuitable.

Once sufficient evidence exists, stop exploring and implement.

## Implementation

Prefer existing mechanisms over new architecture.

For scriptable behavior, prefer an existing `ScriptMgr` / `PlayerScript` hook
over modifying core handlers directly.

If a suitable existing hook is found, do not patch its core call site merely
because that produces fewer changed files.

Before changing code:
- identify the existing hook/API/pattern;
- find one nearby usage when useful;
- reuse the existing mechanism.

For a requested minimal patch, one valid existing hook and one valid public
API/predicate are normally sufficient evidence to implement.

Do not investigate internal implementation details unless required for correctness.

Make the smallest viable patch.

Do not introduce:
- new abstractions;
- new managers;
- new services;
- new hooks;
- new infrastructure

when an existing mechanism is sufficient.

Do not refactor unrelated code.

Once sufficient evidence exists, prefer editing over further investigation.

## Post-edit stop rule

After a successful edit on a small task:

- do not resume repository investigation;
- do not re-investigate APIs/predicates already accepted before the edit;
- do not trace implementation internals merely to validate an already-used public API;
- do not search for alternative implementations;
- do not use Inspect/review-style exploration unless the edit itself failed or the user requested review.

Verification after a small edit is limited to:
- inspect the diff of files changed by the current task;
- optionally inspect the immediately edited lines;
- build/test only if explicitly requested.

If the edit applied successfully and no required verification remains, finish the task.

Never turn post-edit verification into a new research phase.

## Task-specific documentation

Read only documentation relevant to the current task.

Build/configure/tests:

`.agents/docs/build.md`

C++:

`.agents/docs/cpp-guidelines.md`

Work under `src/server/scripts/`:

also read `.agents/docs/cpp-scripts.md`

SQL:

`.agents/docs/sql-guidelines.md`

SmartAI:

also read `.agents/docs/cpp-scripts.md`

PR/code review:

`.agents/docs/code-review.md`

Self-review or PR update:

`.agents/docs/self-review-rules.md`

Subsystem with documentation under:

`.agents/docs/systems/`

Read only its matching document.

e2e:
- `e2e/README.md`
- `.agents/docs/e2e-policy.md`
- `e2e/LLM_GUIDE.md`

Do not preload unrelated documentation.

## Build and validation

Do not configure, build, or run tests unless the user explicitly requests it.

When requested:
- build/test only the smallest relevant target when possible;
- do not rebuild unrelated targets;
- on failure, inspect only the first relevant compiler/test errors;
- do not load or print full build logs;
- fix the relevant error and retry.

For player-visible behavior, prefer live-stack e2e when the local
auth + world + MySQL stack is available.

Do not create e2e for unit-sized logic.

Scratch e2e belongs only in:

`e2e/local/`

Never commit throwaway debug tests.

## SQL

Never edit SQL outside:

`data/sql/updates/pending_db_*/`

unless explicitly requested.

Treat these as immutable:
- `data/sql/base/`
- `data/sql/archive/`
- `data/sql/updates/db_*/`

## Jev

Jev is a cheap decision tool, not a source of repository facts.

Use `mcp__jev__jev_yesno` for genuine yes/no ambiguity.

Use `mcp__jev__jev_choose` when choosing among already-known alternatives.

Good Jev uses:
- deciding whether another expensive investigation is justified;
- choosing between several plausible approaches;
- deciding whether evidence is sufficient to proceed;
- deciding whether another verification step is worthwhile.

Do not use Jev when the answer can be determined directly from:
- source code;
- `rg`;
- Graphify;
- compiler output;
- tests;
- existing documentation.

After a Jev call:
- consume the result silently;
- do not explain or justify it unless requested;
- do not restate the question;
- do not generate additional reasoning merely to explain the score.

If the user explicitly asks to see the Jev result, output only:

`Jev: <decision>, p=<probability>`

## Subagents and workflows

Do not use subagents, delegation, or workflow tools unless explicitly requested
by the user or the task clearly cannot be completed efficiently by the main agent.

For small and medium AzerothCore tasks, prefer a single-agent workflow.

Do not delegate:
- simple repository searches;
- one-file patches;
- finding a hook or API;
- routine debugging;
- straightforward build errors.

## Token discipline

Prefer action over narration.

Do not narrate routine:
- searches;
- file reads;
- tool calls;
- edits;
- retries.

Do not repeatedly state the plan.

Do not summarize architecture unless requested.

Do not paste:
- entire source files;
- large diffs;
- full build logs;
- long tool outputs

into the conversation.

For large tool output, retain only:
- directly relevant lines;
- first relevant errors;
- necessary surrounding context.

Do not repeat code already present in the repository.

Do not continue searching after sufficient evidence exists.

Do not perform unsolicited cleanup or improvements.

Do not generate additional analysis merely to justify an already clear action.

Stop when the requested task is complete and sufficiently verified.

## Graph update

After modifying code, when `graphify-out/graph.json` exists, run:

`graphify update .`

unless the task explicitly does not require repository graph updates.

For small test patches or explicitly temporary changes, do not update Graphify
unless requested.

## Final response

Keep the final response short unless the user requests detail.

Normally report only:
- changed file(s);
- what changed;
- build/test/verification result;
- unresolved issue, if any.

Normally stay within 3–8 lines.