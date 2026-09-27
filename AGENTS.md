# 🎯 GoalOS Agent Master Guidelines & Rules

Welcome to GoalOS. As an AI pair-programmer working on this codebase, you must adhere strictly to the following principles to maintain peak performance, rigorous verification, and continuous improvement.

---

## 1. 🧠 Autonomous Learning & Brain Integration

Before and after every meaningful task:
1. **Consult the Brain:** Check `.agents/brain/system_patterns.md` and `.agents/brain/project_learnings.md` before designing solutions.
2. **Respect Invariants:** Adhere to SQLite context managers, ChromaDB path normalization, 512KB API payload guards, Forest Mist Paper Glass design tokens, and smooth humanized typography (Plus Jakarta Sans + Newsreader).
3. **Continuous Evolution & Autonomous Capture:** Immediately extract and persist all user preferences, styling guidelines, and architectural lessons to `.agents/brain/project_learnings.md` and `.agents/brain/evolution_log.md` without requiring the user to repeat them.

---

## 2. ⚡ Cognitive Collaboration & Pair Programming

- **Preserve Human Reasoning:** Surface consequential architecture, data-model, or algorithm decisions before implementation.
- **Cognitive Delegation:**
  - *Mechanical Work (Autonomous):* Formatting, typing, syntax fixes, repetitive tests, standard boilerplate.
  - *Cognitive Work (Collaborative):* System design, algorithm changes, state machine modifications, schema migrations.
- **Collaboration Loop:** `THINK → EXPLAIN → CHALLENGE → DECIDE → IMPLEMENT → VERIFY → DEBRIEF`.

---

## 3. 🔍 Accuracy & Verification

- **Never Claim Unverified Success:** Never declare a feature working, tested, or fixed without inspecting actual command output or verifying affected files.
- **Deterministic Testing:** Run `pytest -q` or targeted tests when modifying repositories, services, or APIs.
- **Type Safety:** Maintain strict TypeScript types in `frontend/src/` and Pydantic v2 validation in `models/` and `api/`.

---

## 4. 🌿 Autonomous Git Discipline & Version Control

- **Commit every change, no matter how small:** After each edit — including single-line fixes, renames, label/copy tweaks, or a single font-size change — immediately stage and commit it as an atomic Conventional Commit (`feat:`, `style:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`) without waiting for explicit user prompts. Never let verified, working edits sit uncommitted while you move on to the next task.
- **End-of-turn clean-tree check:** Before ending a turn, run `git status --short` one final time. If any file you touched this session is still uncommitted, stage and commit it before finishing — never hand control back with your own edits left uncommitted.
- **Hygiene & Safety:** Verify modified files with `git status --short` before every commit. Never commit secrets (`.env`) or broken code. Stage only the specific files your change touched by name — never `git add -A` or `git add .`.
- **Pre-existing unrelated changes:** If `git status` shows modified or untracked files you did not touch this session, leave them untouched and explicitly name them in your response so the user stays aware — never commit, stash, or discard someone else's in-progress work without being asked.
- **Traceability:** Always report the commit SHA and message in the implementation debrief.

---

## 5. 🛡️ Safety & Non-Destructive Operations

- **Destructive Action Protection:** Never perform irreversible operations (`git push --force`, `rm -rf`, dropping tables without backup, resetting database) without explicit user confirmation.
- **Safe Reset Pattern:** Always use `DataPortabilityService` backup routines before executing database resets.

---

## 6. 📂 Project Reference Links
- Architecture & Spec: [ARCHITECTURE_AND_SPECIFICATIONS.md](file:///C:/Users/jegad/projects/GoalOS/docs/ARCHITECTURE_AND_SPECIFICATIONS.md)
- Project Brain: [Brain README](file:///C:/Users/jegad/projects/GoalOS/.agents/brain/README.md)
- System Patterns: [system_patterns.md](file:///C:/Users/jegad/projects/GoalOS/.agents/brain/system_patterns.md)
- Project Learnings: [project_learnings.md](file:///C:/Users/jegad/projects/GoalOS/.agents/brain/project_learnings.md)
- Git Discipline Rules: [git_discipline.md](file:///C:/Users/jegad/projects/GoalOS/.agents/rules/git_discipline.md)
