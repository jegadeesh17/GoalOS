# GoalOS — Technical Specification

---

## Document Control

| Field | Value |
|-------|-------|
| **Document** | PROJECT_SPEC.md |
| **Version** | 1.0 |
| **Status** | Active |
| **Last updated** | 2026-07-08 |
| **Repository** | [github.com/jegadeesh17/GoalOS](https://github.com/jegadeesh17/GoalOS) |
| **Related docs** | [README.md](../README.md), [DEPLOY.md](../DEPLOY.md), [DEMO.md](./DEMO.md) |

---

## 1. Executive Summary

GoalOS is an **agentic personal coaching system** combining SQLite structured data, ChromaDB vector memory, composite retrieval ranking, and LLM tool-calling. Users log morning/evening journals and long-term goals; the system retrieves relevant memories, invokes coaching pipelines via OpenRouter, and returns structured mentor output with explicit fallbacks when the API is unavailable.

**Interview pitch:**

> *"I built an agentic coaching system with composite memory retrieval, LLM tool-calling for on-demand context, FastAPI deployment, and 70+ pytest tests — with transparent fallbacks when the LLM API is unavailable."*

---

## 2. Scope

### 2.1 In Scope

| # | Capability |
|---|------------|
| 1 | Streamlit multi-page UI (`app/app.py`, `app/pages/`) |
| 2 | SQLite persistence for goals, logs, scores, commitments |
| 3 | ChromaDB vector memory with MiniLM embeddings |
| 4 | Composite retrieval ranking (semantic + importance + recency + frequency) |
| 5 | LLM tool-calling (`search_memories`, `get_active_goals`) |
| 6 | Session pipelines: morning, evening, weekly, reflection |
| 7 | FastAPI `POST /coach/morning` |
| 8 | pytest suite (70+ tests) |
| 9 | Retrieval evaluation report generation |

### 2.2 Out of Scope

- Multi-user authentication / RBAC
- MCP server exposure (tools exist in-process only)
- Fine-tuning base LLM weights
- Automated LLM-judge evaluation at scale

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Module | Status |
|----|-------------|--------|--------|
| FR-01 | Load config from `.env` | `config/settings.py` | ✅ |
| FR-02 | CRUD goals and daily logs | `database/repositories/*` | ✅ |
| FR-03 | Embed and store memories | `services/memory_service.py` | ✅ |
| FR-04 | Composite memory retrieval | `services/memory_service.py` | ✅ |
| FR-05 | Morning agent coach with tools | `ai/pipelines/agent_morning_coach.py` | ✅ |
| FR-06 | Static/evening/weekly pipelines | `ai/pipelines/*` | ✅ |
| FR-07 | OpenRouter client with retries | `ai/openrouter_client.py` | ✅ |
| FR-08 | Graceful API fallbacks | `services/coach_service.py` | ✅ |
| FR-09 | FastAPI morning coach endpoint | `api/main.py` | ✅ |
| FR-10 | Streamlit dashboard | `app/app.py` | ✅ |

### 3.2 Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-01 | pytest completes locally | `pytest -q` |
| NFR-02 | Secrets never committed | `.env` gitignored |
| NFR-03 | CPU embeddings on laptop | MiniLM + hash fallback |
| NFR-04 | Structured JSON coach output | Pydantic models |
| NFR-05 | Offline test isolation | temp DB/Chroma in `tests/conftest.py` |

---

## 4. Architecture

### 4.1 System Context

```text
Streamlit (app/app.py) ──┐
                         ├──▶ CoachService
FastAPI (api/main.py) ───┘         │
                                   ├── MemoryService → ChromaDB + SQLite
                                   ├── AnalyticsService
                                   └── ai/pipelines → OpenRouterClient
                                            │
                                            └── ai/tools.py
```

### 4.2 Layer Pattern

| Layer | Path | Role |
|-------|------|------|
| Repository | `database/repositories/*` | Data access |
| Service | `services/*` | Business logic |
| Pipeline | `ai/pipelines/*` | Prompting + agent loops |
| Tools | `ai/tools.py` | Function schemas + execution |
| UI | `app/app.py`, `app/pages/*` | Streamlit |
| API | `api/main.py` | FastAPI |

### 4.3 RAG Memory Flow

1. **Embed** — `all-MiniLM-L6-v2` via `EmbeddingService`
2. **Store** — dual-write SQLite + ChromaDB
3. **Query** — Chroma cosine search (`n_results = top_k * 3`)
4. **Rank** — 40% semantic + 30% importance + 20% recency + 10% frequency
5. **Generate** — inject into prompt or return via tool calls

---

## 5. Data Model

| Store | Tables / Collections | Content |
|-------|---------------------|---------|
| SQLite | goals, daily_logs, memories, coach_outputs | Structured user data |
| ChromaDB | memory embeddings | Semantic search index |
| Files | `goalos.db`, `chroma_db/` | Local-first persistence |

No public dataset — personal journal import via UI.

---

## 6. API Specification

### `GET /health`

Returns service status and configuration flags.

### `POST /coach/morning`

**Request:**
```json
{ "journal_text": "I planned deep work but meetings took over." }
```

**Response:** Structured JSON with `mentor_rule`, `next_action`, `source`, optional `fallback_reason`.

---

## 7. Evaluation

| Metric | Result | Notes |
|--------|--------|-------|
| pytest | 70+ passing | `pytest -q` |
| Retrieval eval | 0.40/2.0 avg relevance | 5-query manual set; sparse demo corpus |
| Regenerate | `python scripts/generate_retrieval_eval.py` | → `reports/evaluation.md` |

Disclose: personal corpus may be small; eval is rubric-based not production-grade.

---

## 8. Deployment

| Target | Command / Path |
|--------|----------------|
| Local Streamlit | `streamlit run app/app.py` |
| Local API | `uvicorn api.main:app --port 8000` |
| Streamlit Cloud | Main file: `app/app.py` — see [DEPLOY.md](../DEPLOY.md) |
| Docker | `Dockerfile` → `streamlit run app/app.py` |

---

## 9. Testing

```powershell
pytest -q
```

Coverage areas: repositories, memory retrieval, analytics, journal import, API, coach fallbacks.

---

## 10. Known Limitations

- Single-user; no production auth
- Small early corpus reduces retrieval quality
- Manual retrieval eval only
- Agent tool-calling depends on OpenRouter availability

---

## 11. Module Index

| Path | Purpose |
|------|---------|
| `app/bootstrap.py` | Adds project root to `sys.path` for Streamlit |
| `services/coach_service.py` | Coaching orchestration |
| `services/memory_service.py` | Embed, store, retrieve, rank |
| `ai/openrouter_client.py` | HTTP client, JSON parse, tool loop |
| `ai/pipelines/agent_morning_coach.py` | Tool-calling morning pipeline |
| `api/main.py` | FastAPI endpoints |
