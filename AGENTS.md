# AGENTS.md

Customized AzerothCore WotLK 3.3.5a (C++/CMake/MySQL) + Playerbots + custom modules.

## Effort tier (pick once, first, silently)

| Tier | Examples | Load | Budget |
|---|---|---|---|
| T0 answer | question, ID/config lookup, explain snippet, tell me a GM command | nothing | ≤3 tool calls, no plan, answer ≤5 lines |
| T0 live action | level/teleport/learn spell/achievement or other explicitly requested live GM action | `PROJECT.md` only | ≤3 tool calls; use existing operational interface directly |
| T1 small code change | one-file fix, hook callback, log line, code/config/SQL patch | `.agents/skills/azerothcore/SKILL.md` | per skill |
| T2 feature | new module, multi-file, cross-subsystem, unfamiliar system | skill + `PROJECT.md` | per skill |
| Architecture only | design/integration-point question, no edits | architecture workflow + `PROJECT.md` | per workflow |
| Numbered phase | "implement phase N" | `.agents/skills/implement-phase/SKILL.md` | per skill |

Use the lowest tier that fits. Escalate only on concrete evidence.

For T0:
- do not load coding skills;
- do not inspect C++ unless the requested command/behavior cannot be established otherwise;
- do not write a plan;
- do not investigate alternative approaches after one valid path is known.

For T0 live actions:
- the user's explicit mutation request is permission for that requested action only;
- prefer an already configured AzerothMCP/GM/SOAP mechanism;
- never bypass failed command authentication with a direct DB write;
- if the operational interface is unavailable, report the exact manual GM command and stop.

## Hard rules

- Never commit, push, `git reset --hard`, `git clean -fd`, delete directories, or run destructive DB ops unless asked.
- Preserve existing user changes. Touch only files the task needs.
- No build, tests, server restart, SOAP mutation, or live DB write unless asked or the active phase requires it.
- Do not change MCP config, model routing, hooks, permissions, or agent tooling unless that is the task.
## Integration availability

MCP tools and integrations are runtime capabilities.

Do not assume every integration exists as a local command.

For tools such as:
- Jev;
- AzerothMCP;
- external MCP servers;

use them only when available in the current environment.

If unavailable:
- do not search for a CLI executable with the same name;
- do not install or repair integrations during unrelated tasks;
- continue with available tools or report the limitation.

- Never print secrets.
- Core SQL: new files only in `data/sql/updates/pending_db_*/`.
  Never edit `data/sql/base/`, `data/sql/archive/`, `data/sql/updates/db_*/`.
- Bot-to-bot behavior: read BOT_BOT rules in `PROJECT.md` first.
- Style: `.editorconfig` (UTF-8, LF, 120 cols, C++ 4 spaces, JSON/YAML/sh/js 2 spaces).

## Output

Reply in the user's language. Final report ≤8 lines:
changed files, what changed, verification actually run, open items.
Never report PASS for a check that did not run.
