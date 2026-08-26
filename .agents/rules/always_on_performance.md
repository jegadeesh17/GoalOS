# 🚀 Always-On Performance & Verification Standards

As an agent operating within GoalOS, you must maintain an uncompromising engineering standard across every turn.

---

## 1. 🛡️ Verification First, Never Guess
- Never declare an edit "complete", "fixed", or "tested" based solely on reading code or making an edit.
- Run tests (`pytest -q`), inspect build output (`npm run build`), or verify file state before asserting success.
- If an environment restriction prevents live command execution, explicitly state: *"I have verified the syntax and logic via static inspection, but runtime execution could not be performed due to environment limits."*

---

## 2. 🧩 Structural & Type Integrity
- **Backend:** Every Pydantic model in `models/` must specify field types, constraints (`min_length`, `ge`, `le`), and defaults.
- **Frontend:** Avoid `any` types in TypeScript. Use interface definitions that mirror backend Pydantic models.
- **API Contracts:** Maintain exact schema compatibility between FastAPI JSON responses and Axios interface typings in `frontend/src/api/client.ts`.

---

## 3. ⏱️ Latency & Efficiency Standards
- Always keep database operations indexed: `goals(status, horizon)`, `memories(content_hash, status)`, `daily_logs(date)`.
- Avoid N+1 queries. Use batch repository methods (e.g. `MilestoneRepository.get_for_goals(goal_ids)` or joined queries) where applicable.
- Vector search must default to top_k with MMR diversity pruning to minimize payload overhead.
