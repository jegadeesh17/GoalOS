# GoalOS — Interactive Demo & Evaluation Walkthrough

5-minute walkthrough for the GoalOS Executive Life Operating System and Agentic AI Coaching Platform.

---

## Prerequisites

```bash
pip install -r requirements.txt
cd frontend && npm install && cd ..
# Optional: set OPENROUTER_API_KEY in .env for live LLM completions
```

---

## 1. Automated Quality Suite (30 sec)

```bash
pytest -q
```

**Expected Result:** **106/106 tests passing (100%)** across repositories, 5-factor hybrid RAG, Life Calendar, multi-agent Coordinator, Coach Chat, sessions blackboard, telemetry, and rate limiters.

---

## 2. 5-Factor Cognitive Retrieval Eval (1 min)

```bash
python scripts/generate_retrieval_eval.py
type reports\evaluation.md
```

**Talking Points:**
- 5-factor composite formula: $0.35 \cdot S_{\text{sem}} + 0.15 \cdot S_{\text{lex}} + 0.25 \cdot S_{\text{imp}} + 0.15 \cdot S_{\text{rec}} + 0.10 \cdot S_{\text{freq}}$.
- Maximal Marginal Relevance (MMR) text similarity pruning ($> 0.94$ cosine similarity rejected for diversity).
- Dual-write persistence to SQLite (`memories` + `memory_fts`) and ChromaDB vector embeddings.

---

## 3. FastAPI & Multi-Agent Coordinator Demo (1.5 min)

```bash
python -m uvicorn api.main:app --reload --port 8000
```

### A. Health & Diagnostics:
```bash
curl http://127.0.0.1:8000/health
```

### B. Structured Morning Coach:
```bash
curl -X POST http://127.0.0.1:8000/coach/morning -H "Content-Type: application/json" -d "{\"gratitude\":\"Grateful for uninterrupted focus\",\"tasks\":[{\"text\":\"Ship portfolio architecture docs\",\"priority\":1}]}"
```
Point out structured JSON response: `mentor_rule`, `tools_used`, `source` (`ai_agent` or deterministic fallback), and grounded citations.

### C. Multi-Agent Coordinator Chat Turn:
```bash
curl -X POST http://127.0.0.1:8000/coach/chat -H "Content-Type: application/json" -d "{\"message\":\"What are my active goals and how is my pacing?\"}"
```
Point out intent classification (`goals_pacing`), scoped tool calls (`get_active_goals`), blackboard state, latency, and telemetry trace generation.

---

## 4. React 18 Desktop Dashboard Walkthrough (2 min)

Launch the unified environment:
```cmd
run_app.bat
```
*(Or in a separate terminal: `cd frontend && npm run dev` $\rightarrow$ open `http://localhost:5173`)*

### Key Views to Highlight:
1. **Life Calendar (Memento Mori):** 3,640 discrete week blocks (52 weeks × 70 years) calculating lived vs. remaining weeks with decade markers.
2. **Daily Journal & Tasks:** Morning planning (sleep, mood, intentions, top priority, goal-linked tasks) and evening retrospective (wins, lessons, deep work hours).
3. **Multi-Horizon Goals:** 1-Month Sprints, 1-Year Horizons, and 5-Year Visions with interactive milestone progress.
4. **AI Coach Studio:**
   - **Guided Pipelines:** Morning, Evening, Weekly, Future Self, and Goal Alignment.
   - **Coach Chat:** Conversational multi-agent thread backed by session history and scoped tool execution.
5. **Analytics & Patterns:** Vital averages, daily deterministic growth scores, and multi-day behavioral pattern detection.
6. **Cognitive Memories:** Hybrid search explorer with real-time composite ranking.
7. **Settings & Sovereign Privacy:** User profile, life visions, one-switch remote AI consent, and safe factory reset with automated SQLite backup.

---

## Verification Checklist

- [ ] `pytest -q` is 100% green (106 tests passing)
- [ ] Backend starts cleanly on `http://localhost:8000`
- [ ] Frontend starts cleanly on `http://localhost:5173`
- [ ] `/health` returns status and row counts
- [ ] Morning coach and Coach Chat execute and return structured output
- [ ] Life Calendar renders 3,640 interactive week blocks smoothly in Forest Mist Paper Glass theme
