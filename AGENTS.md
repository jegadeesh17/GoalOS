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

- **Autonomous Commits:** Upon concluding any meaningful code change, refactor, or style update, automatically stage verified files and create atomic Conventional Commits (`feat:`, `style:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`) without waiting for explicit user prompts.
- **Hygiene & Safety:** Verify modified files with `git status --short` before committing. Never commit secrets (`.env`) or broken code.
- **Traceability:** Always report the commit message and summary in the implementation debrief.

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
