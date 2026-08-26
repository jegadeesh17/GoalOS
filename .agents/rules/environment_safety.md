# 🛡️ Environment & Execution Safety Rules

Guidelines for executing commands, interacting with the file system, and operating within Windows / PowerShell environments.

---

## 1. 🪟 Windows & PowerShell Execution Guidelines
- **Path Separators:** Always be prepared for Windows backslashes (`\`) vs POSIX slashes (`/`). Use `pathlib.Path` in Python and forward slashes in markdown URLs (`file:///C:/Users/...`).
- **Command Formatting:** Prefer simple, prefix-matchable command shapes (`python -m ...`, `npm run ...`, `pytest ...`). Avoid complex variable interpolations in command strings when direct parameters work.

---

## 2. ⛔ Destructive Command Gates
Never execute the following without explicit, unambiguous user instruction:
- `git push --force` or `git reset --hard`
- `rm -rf`, `Remove-Item -Recurse -Force` on non-empty directories
- Dropping production tables or bypassing migration versioning
- Overwriting uncommitted workspace files

---

## 3. 🧪 Isolation & Test Cleanliness
- Tests must never touch the live `goalos.db` or `chroma_db/` directories.
- Always use temporary database fixtures provided in `tests/conftest.py` (`temp_db`).
