# AGENTS.md

AzerothCore is a C++ World of Warcraft 3.3.5a server emulator using CMake and MySQL.

## Global rules

For any non-trivial AzerothCore codebase task, load and follow:

`.agents/skills/azerothcore/SKILL.md`

Do not configure, build, or run tests unless explicitly requested.
When requested, use the smallest relevant target.

Never edit SQL outside `data/sql/updates/pending_db_*/` unless explicitly requested.
Treat `data/sql/base/`, `data/sql/archive/`, and `data/sql/updates/db_*/` as immutable.

Follow `.editorconfig`:
UTF-8, LF, max 120 columns, trailing newline, no trailing whitespace.
Use 4 spaces for C++; 2 spaces for JSON/YAML/sh/ts/js.

Make the smallest viable patch.
Reuse existing AzerothCore hooks, APIs, patterns, and architecture.
Do not create new architecture when an existing mechanism is sufficient.
Do not modify unrelated code.

Do not dump entire large files, diffs, or logs into context.
Do not repeat equivalent searches or reread unchanged code without reason.
Do not narrate routine tool calls.
Prefer implementation over commentary once enough evidence is available.

Stop when the requested task is complete and sufficiently verified.

If a planning document is needed, place it under:

`.agents/plans/<task-slug>/`

If the user explicitly requests `/graphify`, load the AzerothCore skill first.

Final responses should normally be concise:
changed files, change made, verification result, and any unresolved issue.