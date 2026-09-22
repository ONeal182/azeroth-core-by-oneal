# AGENTS.md

AzerothCore is a C++ World of Warcraft 3.3.5a server emulator using CMake and MySQL.

## Global rules

For any non-trivial AzerothCore codebase task, load and follow:

`.agents/skills/azerothcore/SKILL.md`

The AzerothCore skill is the authoritative source for:
- search strategy;
- investigation budgets;
- tool-selection workflow;
- Jev usage;
- post-edit stopping rules;
- token/context discipline.

Do not duplicate or override those workflow rules elsewhere.

Do not configure, build, or run tests unless explicitly requested.
When requested, use the smallest relevant target.

Never edit SQL outside `data/sql/updates/pending_db_*/` unless explicitly requested.

Treat these as immutable:
- `data/sql/base/`
- `data/sql/archive/`
- `data/sql/updates/db_*/`

Follow `.editorconfig`:
- UTF-8;
- LF;
- max 120 columns;
- trailing newline;
- no trailing whitespace;
- C++: 4 spaces;
- JSON/YAML/sh/ts/js: 2 spaces.

Make the smallest viable patch.

Reuse existing AzerothCore hooks, APIs, patterns, and architecture.

Do not create new architecture when an existing mechanism is sufficient.

Do not modify unrelated code.

Preserve existing user changes.

Never commit, push, run `git reset --hard`, run `git clean -fd`,
or delete major project directories unless explicitly requested.

Do not modify MCP configuration, model/API routing, hooks, permissions,
or optimization tooling during ordinary coding tasks unless explicitly requested.

Never expose secrets.

Do not dump entire large files, diffs, or logs into context.

Do not narrate routine tool calls.

Stop when the requested task is complete and sufficiently verified.

If a planning document is needed, place it under:

`.agents/plans/<task-slug>/`

Final responses should normally be concise:
- changed files;
- what changed;
- verification performed;
- anything unresolved.