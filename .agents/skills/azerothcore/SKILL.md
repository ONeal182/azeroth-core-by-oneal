---
name: azerothcore
description: >
  Coding, debugging, SQL, modules, playerbots, build/test work in this AzerothCore repo.
---

# AzerothCore workflow

Tier comes from `AGENTS.md`. Read `PROJECT.md` only for T2, BOT_BOT, DB schema, or new-module work.

## T1 — small change

Goal: minimum facts → patch → stop.

1. Facts needed, nothing more: entry point/hook, API to call, guards/exclusions, file to edit.
2. Search exact symbols in a scoped path with a type filter:
   `rg -n "OnPlayerLogin\(" src/server/game -g "*.h"`.
   No broad terms (`player`, `bot`, `script`), no large OR-regexes.
3. Budget before first edit: 4 searches + 2 reads. Failed ones count. It is a ceiling, not a target.
4. One declaration + one usage = fact resolved. Never re-check a resolved fact.
5. Name not found after 2 searches → read the one likely owning header. Still missing → stop, report that one fact.
6. First integration point matching the exact lifecycle wins (login ≠ enter-world, create ≠ spawn, init ≠ update).
   Do not compare alternatives once one is valid.
7. Prefer ScriptMgr / PlayerScript / module hook over a core edit. No new managers, services, hooks, frameworks.
8. After the edit: `git diff -- <file>` only. No new research, no "better" rewrite. Stop.

## T2 — feature / cross-subsystem

- Architecture: `graphify query "<q>"` first if `graphify-out/graph.json` exists; `path`/`explain` only when needed.
  Failed once → fall back to `rg`, do not retry.
- Graphify is orientation, not proof. Confirm lifecycle/semantics in source (clangd or a targeted read).
- Read only relevant function ranges, never whole large files.
- Tracer bullet first: one trigger → behavior → persistence → verification working before adding breadth.
- Keep `.agents/docs/features/<feature>/` describing implemented reality only (not plans).

## Tools

| Need | Tool |
|---|---|
| exact string, config key, SQL name, log text | `rg` |
| definition, references, callers, inheritance | clangd |
| subsystem relationships, impact | Graphify |
| creature / item / spell / quest / SmartAI / DB-row facts | AzerothMCP — not source search |
| genuine choice between known valid options | Jev, once. Never for facts, never to override a rule here |

## Docs (load only on match; `.agents/docs/` unless a path is given)

- build / config / tests: `build.md`
- C++: `cpp-guidelines.md`; `src/server/scripts/` or SmartAI: also `cpp-scripts.md`
- SQL: `sql-guidelines.md`
- review: `code-review.md`; self-review / PR update: `self-review-rules.md`
- e2e: `e2e/README.md` + `e2e-policy.md`

## SQL

- Core: new files only in `data/sql/updates/pending_db_*/`.
- Module: copy the layout of a similar module's `data/sql/`. Verify the real schema first; use explicit column lists.
- Module SQL auto-apply hazard: see `PROJECT.md` → Known gotchas.

## Verification (only when asked)

Smallest target, existing build config. Save long logs to a file; read the first real error.
Report source-check / build / tests / runtime separately. Compiling ≠ gameplay correct.

## Subagents

Main agent only for T0/T1. Subagent only for large, independently parallel investigations.

## Stop

Ask only if: a missing requirement changes the result, a fact is unobtainable, an action is destructive/irreversible,
or work leaves scope. Otherwise continue to done, then stop — no adjacent improvements, no next phase.
