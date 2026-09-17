# clangd compilation database issue

Visual Studio generator doesn't export proper compile_commands.json.
Creating separate Ninja build requires MSVC environment that Git Bash doesn't inherit.

## Workaround options:

1. **Use clangd without full compilation database** (current)
   - Basic navigation works
   - Some features limited

2. **Generate from existing VS build**
   ```bash
   python -m pip install compdb
   python -m compdb -p build list > compile_commands.json
   ```
   Currently fails: VS build doesn't have compilation database to extract.

3. **Create Ninja build from Developer Command Prompt** (requires manual step)
   ```cmd
   "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
   cmake -S . -B build-clangd -G Ninja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
   ```

4. **Use Graphify as primary navigation** (recommended)
   - 32K nodes already indexed
   - Faster than clangd for architecture queries
   - clangd as fallback for precise definition lookups

Current setup uses option 1 + 4.
