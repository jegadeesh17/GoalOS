# 🌿 Git Discipline & Version Control Standards

This document establishes the mandatory Git workflows, commit standards, and safety invariants for GoalOS.

---

## 1. 🎯 Core Git Principles

1. **Clean Working Tree:** Never leave untracked artifacts, temporary files, or uncommitted half-baked edits without logging their state.
2. **Atomic Commits:** Each commit must encapsulate a single logical change. Do not bundle unrelated refactors, bug fixes, and documentation updates into monolithic commits.
3. **Verified Before Staged:** Never commit code that has syntax errors, broken imports, or failing tests.
4. **Secret Protection:** Never stage or commit `.env`, private keys, API credentials, or credentials files. Keep `.gitignore` strictly honored.

---

## 2. 📝 Conventional Commits Standard

All commit messages MUST follow the Conventional Commits specification:

```
<type>(<optional-scope>): <imperative short description>

[optional body explaining rationale and trade-offs]

[optional footer(s)]
```

### Allowed Types:
- `feat`: New feature or user-facing capability (e.g. `feat(coach): add future self 10-year alignment pipeline`)
- `fix`: Bug fix or error resolution (e.g. `fix(memory): normalize ChromaDB path resolution on Windows`)
- `docs`: Documentation updates or specifications (e.g. `docs(spec): add high-level architecture & specifications document`)
- `refactor`: Code restructuring without behavioral change (e.g. `refactor(api): extract daily score calculation to helper`)
- `perf`: Performance optimization (e.g. `perf(calendar): remove backdrop blur on 3640-week discrete grid`)
- `test`: Adding or modifying tests (e.g. `test(memory): add 5-factor composite ranking unit tests`)
- `chore`: Maintenance, dependencies, brain updates, or git configuration (e.g. `chore(brain): initialize autonomous memory graph and rules`)

---

## 3. 🔄 Continuous Post-Edit Git Workflow

When completing a task or upon explicit request to update GitHub:

```
+-----------------------------------------------------------------------------------+
|  STEP 1: INSPECT STATUS                                                           |
|  - Execute: git status --short                                                    |
|  - Verify all modified and untracked files are intentional.                       |
+-----------------------------------------------------------------------------------+
                                      │
                                      ▼
+-----------------------------------------------------------------------------------+
|  STEP 2: PRE-COMMIT VERIFICATION                                                 |
|  - Run lints/tests or static analysis to ensure zero syntax regressions.         |
|  - Ensure no secrets (.env, API keys) are staged.                                |
+-----------------------------------------------------------------------------------+
                                      │
                                      ▼
+-----------------------------------------------------------------------------------+
|  STEP 3: ATOMIC STAGING & COMMIT                                                 |
|  - Stage targeted files: git add <files>                                          |
|  - Commit with conventional message: git commit -m "<type>(<scope>): <msg>"       |
+-----------------------------------------------------------------------------------+
                                      │
                                      ▼
+-----------------------------------------------------------------------------------+
|  STEP 4: SAFE SYNC TO REMOTE                                                      |
|  - Push to remote branch: git push origin <branch>                                |
|  - Verify push was clean and report the commit SHA in the debrief.                |
+-----------------------------------------------------------------------------------+
```

---

## 4. ⛔ Non-Destructive Safety Invariants

The following operations are strictly gated and require explicit confirmation:
- `git push --force` or `git push -f`
- `git reset --hard`
- `git clean -fdx`
- `git branch -D`
- Rebasing shared/public branches

Always favor forward-moving, non-destructive commits and branches.
