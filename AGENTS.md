# 🎯 GoalOS Agent Master Guidelines & Rules

Welcome to GoalOS. As an AI pair-programmer working on this codebase, you must adhere strictly to the following principles to maintain peak performance, rigorous verification, and continuous improvement.

---

## 1. 🧠 Autonomous Learning & Brain Integration

Before and after every meaningful task:
1. **Consult the Brain:** Check `.agents/brain/system_patterns.md` and `.agents/brain/project_learnings.md` before designing solutions.
2. **Respect Invariants:** Adhere to SQLite context managers, ChromaDB path normalization, 512KB API payload guards, and celestial light UI tokens.
3. **Continuous Evolution:** After resolving non-trivial issues or adding features, extract lessons and log reflections to `.agents/brain/evolution_log.md` and `.agents/brain/project_learnings.md` (or run `.agents/brain/update_brain.py`).

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

## 4. 🌿 Git Discipline & Version Control

- **Atomic Commits:** Follow Conventional Commits format (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`).
- **Hygiene & Verification:** Verify changes with `git status --short` before committing. Never commit secrets (`.env`) or broken code.
- **Post-Edit Sync:** When updating GitHub or completing work, stage cleanly, commit with a descriptive message, and push safely.

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
