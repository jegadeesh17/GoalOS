# 📈 Continuous Learning & Self-Improvement Protocol

GoalOS uses a dynamic learning loop so that the AI assistant continuously gets sharper, learns repository nuances, and avoids repeating past bugs.

---

## 1. 🔄 The 4-Step Prompt Learning Loop

```
+-----------------------------------------------------------------------------------+
|  STEP 1: INGESTION & BRAIN CONSULTATION                                           |
|  - Check .agents/brain/system_patterns.md and project_learnings.md.               |
|  - Identify if similar issues or patterns occurred previously.                    |
+-----------------------------------------------------------------------------------+
                                      │
                                      ▼
+-----------------------------------------------------------------------------------+
|  STEP 2: EXECUTION & VERIFICATION                                                |
|  - Implement changes adhering strictly to established patterns.                   |
|  - Run verification (tests, schema validations, inspections).                     |
+-----------------------------------------------------------------------------------+
                                      │
                                      ▼
+-----------------------------------------------------------------------------------+
|  STEP 3: LEARNING EXTRACTION                                                      |
|  - Did we encounter a new edge case, library quirk, or design insight?            |
|  - If YES: format the finding as a structured learning.                          |
+-----------------------------------------------------------------------------------+
                                      │
                                      ▼
+-----------------------------------------------------------------------------------+
|  STEP 4: PERSISTENCE INTO BRAIN                                                   |
|  - Append to .agents/brain/project_learnings.md or evolution_log.md.             |
|  - Or run: python .agents/brain/update_brain.py --add-learning ...                |
+-----------------------------------------------------------------------------------+
```

---

## 2. 📝 What Qualifies as a Worthy Learning?
Record learnings whenever you discover:
1. **Library Quirks:** Undocumented behaviors in ChromaDB, SQLite FTS5, FastAPI, Vite, or Pydantic.
2. **Performance Bottlenecks:** Memory leaks, N+1 query patterns, rendering latency on 3,640-grid components.
3. **Refactoring Gotchas:** Edge cases in date math, week calculation boundaries, timezone handling, or HMAC token comparison.
4. **Architectural Lessons:** Why an alternative approach failed or proved too brittle.

---

## 3. 🎯 Rule: No Passive Regressions
Never re-introduce an anti-pattern that is explicitly documented in `.agents/brain/troubleshooting_kb.md` or `.agents/brain/system_patterns.md`.
