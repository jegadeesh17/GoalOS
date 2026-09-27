# 🌿 Git Discipline & Version Control Standards

This document establishes the mandatory Git workflows, commit standards, and safety invariants for GoalOS.

---

## 1. 🎯 Core Git Principles

1. **Clean Working Tree, Always:** After every edit — however minor — commit it before starting the next one. The working tree should be clean (or contain only pre-existing, explicitly-flagged changes that aren't yours) at the start and end of every turn.
2. **Atomic Commits:** Each commit must encapsulate a single logical change. Do not bundle unrelated refactors, bug fixes, and documentation updates into monolithic commits. Conversely, do not defer committing a finished, verified change just because a follow-up change is coming — commit each one as it lands.
3. **Verified Before Staged:** Never commit code that has syntax errors, broken imports, or failing tests.
4. **Secret Protection:** Never stage or commit `.env`, private keys, API credentials, or credentials files. Keep `.gitignore` strictly honored.
5. **Own Your Files Only:** Stage by explicit filename, never `git add -A`/`git add .`. If `git status` shows edits you didn't make this session, leave them alone and name them to the user — don't fold someone else's in-progress work into your commit, and don't commit, stash, or discard it unasked.

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

## 3. 🔄 Autonomous Continuous Post-Edit Git Workflow

Upon concluding ANY code change — a full feature, a one-line fix, a renamed variable, a single CSS value — the AI agent autonomously executes the following workflow without requiring user prompts. "It was a small change" is never a reason to skip or defer this loop.

```
+-----------------------------------------------------------------------------------+
|  STEP 1: INSPECT STATUS                                                           |
|  - Execute: git status --short                                                    |
|  - Verify all modified and untracked files are intentional.                       |
|  - Separate YOUR edits from any pre-existing changes already sitting in the tree. |
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
|  - Stage targeted files by name: git add <files>  (never -A / .)                  |
|  - Commit with conventional message: git commit -m "<type>(<scope>): <msg>"       |
+-----------------------------------------------------------------------------------+
                                      │
                                      ▼
+-----------------------------------------------------------------------------------+
|  STEP 4: SAFE SYNC TO REMOTE                                                      |
|  - Push to remote branch: git push origin <branch>                                |
|  - Verify push was clean and report the commit SHA in the debrief.                |
+-----------------------------------------------------------------------------------+
                                      │
                                      ▼
+-----------------------------------------------------------------------------------+
|  STEP 5: END-OF-TURN RE-CHECK                                                     |
|  - Before ending the turn, re-run: git status --short                             |
|  - If anything you touched is still uncommitted, return to STEP 2. Do not finish  |
|    a turn with your own verified edits left uncommitted.                          |
+-----------------------------------------------------------------------------------+
```

If files you did not touch this session appear in `git status`, do not add them to your commit, stash them, or discard them — name them explicitly to the user instead, and let your own commit go through on its own targeted file list.

---

## 4. ⛔ Non-Destructive Safety Invariants

The following operations are strictly gated and require explicit confirmation:
- `git push --force` or `git push -f`
- `git reset --hard`
- `git clean -fdx`
- `git branch -D`
- Rebasing shared/public branches

Always favor forward-moving, non-destructive commits and branches.
