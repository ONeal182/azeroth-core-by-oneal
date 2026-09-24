# AGENTS.md

Customized AzerothCore WotLK 3.3.5a (C++/CMake/MySQL) + Playerbots + custom modules.

## Effort tier (pick once, first, silently)

| Tier | Examples | Load | Budget |
|---|---|---|---|
| T0 answer | question, lookup, ID/config value, GM command, explain a snippet | nothing | ≤3 tool calls, no plan, answer ≤5 lines |
| T1 small change | one-file fix, hook callback, log line, command, config/SQL row | `.agents/skills/azerothcore/SKILL.md` | per skill |
| T2 feature | new module, multi-file, cross-subsystem, unfamiliar system | skill + `PROJECT.md` | per skill |
| Architecture only | design / integration-point question, no edits | `.agents/skills/azerothcore-architecture/SKILL.md` + `PROJECT.md` | per skill |
| Numbered phase | "implement phase N" | `.agents/skills/implement-phase/SKILL.md` | per skill |

Use the lowest tier that fits. Escalate only on concrete evidence (e.g. the fix turns out to span subsystems).
For T0/T1: no restating the task, no written plan, no deliberation between equally valid options —
take the first valid one.

## Hard rules

- Never commit, push, `git reset --hard`, `git clean -fd`, delete directories, or run destructive DB ops unless asked.
- Preserve existing user changes. Touch only files the task needs.
- No build, tests, server restart, SOAP mutation, or live DB write unless asked or the active phase requires it.
- Do not change MCP config, model routing, hooks, permissions, or agent tooling unless that is the task.
- Never print secrets.
- Core SQL: new files only in `data/sql/updates/pending_db_*/`.
  Never edit `data/sql/base/`, `data/sql/archive/`, `data/sql/updates/db_*/`.
- Bot-to-bot behavior: read BOT_BOT rules in `PROJECT.md` first.
- Style: `.editorconfig` (UTF-8, LF, 120 cols, C++ 4 spaces, JSON/YAML/sh/js 2 spaces).

## Output

Reply in the user's language. Final report ≤8 lines:
changed files, what changed, verification actually run, open items.
Never report PASS for a check that did not run.
