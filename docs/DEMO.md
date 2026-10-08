# GoalOS — Interactive Demo & Evaluation Walkthrough

5-minute walkthrough for the GoalOS Executive Life Operating System and Agentic AI Coaching Platform.

---

## Prerequisites

```bash
pip install -r requirements-dev.txt
cd frontend && npm install && cd ..
# Optional: set OPENROUTER_API_KEY in .env for live LLM completions
```

---

## 1. Automated Quality Suite (30 sec)

```bash
pytest -q
```

**Expected Result:** the suite collects 276 tests across repositories, 5-factor hybrid RAG, Life Calendar, the Coordinator, Coach Chat, session blackboard, telemetry, monthly analytics, task links and yearly pacing. The README's "Running tests" section holds the latest measured result; this guide does not repeat a count.

---

## 2. 5-Factor Cognitive Retrieval Eval (1 min)

```bash
python scripts/generate_retrieval_eval.py
type reports\evaluation.md   # Windows; the script writes this git-ignored file
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
curl http://127.0.0.1:8000/health/details
```
`/health` returns only `{"status":"ok"}`. `/health/details` adds `openrouter_configured`, `remote_ai_consent`, and the `log_count`, `memory_count` and `goal_count` row counts.

### B. Goal Alignment (Monthly Pacing):
```bash
curl -X POST http://127.0.0.1:8000/coach/progress -H "Content-Type: application/json" -d "{\"date\":\"2026-09-15\"}"
```
Point out that it paces the month's logged days against active 1-month and 1-year goals, and that without remote AI consent it returns a deterministic fallback with `fallback_reason`.

### C. Multi-Agent Coordinator Chat Turn:
```bash
curl -X POST http://127.0.0.1:8000/coach/chat -H "Content-Type: application/json" -d "{\"message\":\"What are my active goals and how is my pacing?\"}"
```
Point out the keyword-based intent classification (`goals_pacing`), the blackboard state, the latency, and the trace id. Without remote AI consent and an API key the reply comes from the local rule engine (`source: deterministic_rules`, `tools_used: []`, with a `fallback_reason`). With consent and a key, the server first reads the matching data itself (active goals, recent logs, memories) and the response's `tools_used` lists those reads; the model does not choose tools, and telemetry spans are written for the LLM call.

---

## 4. React 18 Desktop Dashboard Walkthrough (2 min)

Launch the unified environment:
```cmd
run_app.bat
```
*(Or in a separate terminal: `cd frontend && npm run dev` $\rightarrow$ open `http://localhost:5173`)*

### Key Views to Highlight:
1. **Life Calendar (Memento Mori):** 3,640 discrete week blocks (52 weeks × 70 years) calculating lived vs. remaining weeks with decade markers.
2. **Journal:** Six-section notebook entries (Gratitude, Awake, Plan, Tasks, Review, Takeaway). Click any calendar day to open its full entry in the day drawer.
3. **Multi-Horizon Goals:** 1-Month, 1-Year, 5-Year, and 10-Year horizons with interactive milestone progress.
4. **AI Coach Studio:**
   - **Guided Pipelines:** Goal Alignment (monthly/yearly pacing) and Future Self (5/10-year pacing).
   - **Coach Chat:** Conversational thread backed by session history and a shared blackboard; context is fetched by the server according to keyword-detected intent.
5. **Analytics & Patterns:** Vital averages, daily deterministic growth scores, and multi-day behavioral pattern detection.
6. **Cognitive Memories:** Hybrid search explorer with real-time composite ranking.
7. **Settings & Sovereign Privacy:** User profile (birth date, target age), one-switch remote AI consent, and safe factory reset with automated SQLite backup.

---

## Verification Checklist

- [ ] `pytest -q` result matches the README's "Running tests" section
- [ ] Backend starts cleanly on `http://localhost:8000`
- [ ] Frontend starts cleanly on `http://localhost:5173`
- [ ] `/health` returns `{"status":"ok"}` and `/health/details` returns the row counts
- [ ] Goal Alignment, Future Self, and Coach Chat execute and return structured output
- [ ] Life Calendar renders 3,640 interactive week blocks smoothly in Forest Mist Paper Glass theme
