# GoalOS — Project Specification & Requirements

---

## Document Control

| Field | Value |
|-------|-------|
| **Document** | PROJECT_SPEC.md |
| **Version** | 2.6.0 (Unified Executive OS Edition) |
| **Status** | Active & Implemented in Production |
| **Last updated** | 2026-09-03 |
| **Repository** | [github.com/jegadeesh17/GoalOS](https://github.com/jegadeesh17/GoalOS) |
| **Related docs** | [ARCHITECTURE_AND_SPECIFICATIONS.md](./ARCHITECTURE_AND_SPECIFICATIONS.md), [SYSTEM_DESIGN_MAPPING.md](./SYSTEM_DESIGN_MAPPING.md), [README.md](../README.md), [DEPLOY.md](../DEPLOY.md), [DEMO.md](./DEMO.md) |

---

## 1. Executive Summary

GoalOS is an **agentic personal coaching and life operating system** combining SQLite structured data, ChromaDB vector memory, 5-factor composite retrieval ranking, and multi-agent LLM tool-calling. Users engage with a desktop web interface (React 18 + Vite) featuring a 70-year Life Calendar, morning/evening journals, multi-horizon goals, cognitive memories, and AI coaching.

The system retrieves relevant memories using hybrid lexical and vector search, invokes coaching pipelines or conversational multi-agent chat via OpenRouter, and returns structured mentor output with transparent deterministic fallbacks when offline or when remote AI consent is disabled.

**Interview pitch:**

> *"I built an executive life operating system with a 70-year Memento Mori calendar, 5-factor hybrid RAG retrieval, a supervisor-coordinator multi-agent coaching engine with scoped toolkits and session blackboards, a FastAPI backend with 512KB payload protection, and 106 pytest tests — with transparent deterministic fallbacks when offline."*

---

## 2. Scope

### 2.1 In Scope

| # | Capability | Implementation Location |
|---|------------|-------------------------|
| 1 | **Desktop SPA:** React 18 + TypeScript + Vite with Forest Mist Paper Glass design system | `frontend/src/` |
| 2 | **70-Year Life Calendar (Memento Mori):** 3,640 discrete week blocks (52 weeks × 70 years) | `frontend/src/components/LifeCalendar.tsx`, `services/life_calendar_service.py` |
| 3 | **Daily Journal & Execution:** Morning planning (sleep, mood, priorities, tasks) & evening retrospective | `frontend/src/components/JournalView.tsx`, `database/repositories/log_repository.py` |
| 4 | **Multi-Horizon Goals:** 1-Month Sprints, 1-Year Horizons, 5-Year Visions with milestone checklists | `frontend/src/components/GoalsView.tsx`, `database/repositories/goal_repository.py` |
| 5 | **AI Coaching Suite:** 5 guided pipelines (Morning, Evening, Weekly, Future Self, Goal Alignment) | `frontend/src/components/AICoachView.tsx`, `services/coach_service.py` |
| 6 | **Multi-Agent Coordinator & Chat:** Intent triage, domain-scoped toolkits, session blackboard | `ai/pipelines/coordinator.py`, `ai/tools/*`, `database/repositories/coach_session_repository.py` |
| 7 | **Cognitive Memory Base (Hybrid RAG):** Dual-write SQLite + ChromaDB with 5-factor ranking and MMR pruning | `services/memory_service.py`, `database/repositories/memory_repository.py` |
| 8 | **Longitudinal Analytics & Behavioral Patterns:** Daily growth scores & multi-day pattern detection | `services/analytics_service.py`, `services/pattern_service.py` |
| 9 | **Sovereign Privacy & Data Portability:** Remote AI consent switch, JSON export, auto-backup factory reset | `services/settings_service.py`, `services/data_portability_service.py` |
| 10 | **FastAPI REST API:** Full CRUD, 512KB payload ceiling, CORS, and constant-time HMAC token auth | `api/main.py` |
| 11 | **Comprehensive Test Suite:** 106 passing tests across repositories, services, pipelines, and API | `tests/*` |
| 12 | **Production AI Evaluation Framework:** 6 Vision Metrics and leaky-bucket rate limiting for free-tier LLMs | `ai/eval/*`, `scripts/run_model_eval.py` |

### 2.2 Out of Scope

- Multi-tenant cloud SaaS hosting or remote user identity providers (single-user sovereign local-first by architectural mandate).
- Base LLM weight fine-tuning.
- Real-time multi-user synchronization or cloud-managed databases.

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Implementation Module | Status |
|----|-------------|-----------------------|:------:|
| **FR-01** | Load system settings and credentials securely from `.env` | `config/settings.py` | ✅ |
| **FR-02** | 70-Year Memento Mori lifespan calculation (3,640 discrete weeks) | `services/life_calendar_service.py` | ✅ |
| **FR-03** | Daily log upsert with automatic scoring recalculation | `api/main.py::upsert_journal_entry` | ✅ |
| **FR-04** | Multi-horizon goal management (1M, 1Y, 5Y) with cascading milestones | `database/repositories/goal_repository.py` | ✅ |
| **FR-05** | Dual-write memories to SQLite (`memories`, `memory_fts`) and ChromaDB | `services/memory_service.py` | ✅ |
| **FR-06** | 5-Factor hybrid RAG retrieval with MMR diversity pruning | `services/memory_service.py` | ✅ |
| **FR-07** | Execute 5 structured coaching pipelines with grounded evidence | `ai/pipelines/*`, `services/coach_service.py` | ✅ |
| **FR-08** | Multi-agent conversational coaching with session blackboard | `ai/pipelines/coordinator.py` | ✅ |
| **FR-09** | Scoped domain toolkits (`JournalToolkit`, `GoalsToolkit`, `MemoryToolkit`, `CalendarToolkit`) | `ai/tools/*` | ✅ |
| **FR-10** | Deterministic rule fallback when offline or consent disabled | `services/coach_service.py`, `ai/pipelines/coordinator.py` | ✅ |
| **FR-11** | OpenRouter integration with leaky-bucket rate limiting | `ai/openrouter_client.py`, `ai/eval/rate_limiter.py` | ✅ |
| **FR-12** | Telemetry and estimated USD spend tracking | `services/observability_service.py` | ✅ |
| **FR-13** | One-click JSON data export and safe factory reset with auto-backup | `services/data_portability_service.py` | ✅ |
| **FR-14** | Responsive React 18 SPA with Forest Mist design system | `frontend/src/*` | ✅ |

### 3.2 Non-Functional Requirements

| ID | Requirement | Target Specification | Enforcement Mechanism |
|----|-------------|----------------------|-----------------------|
| **NFR-01** | Test Suite Completeness | 100% green local test suite | `pytest -q` (106 passing tests) |
| **NFR-02** | Data Privacy & Zero Leakage | Sovereign local persistence; explicit AI opt-in | `remote_ai_consent` gate in `SettingsService` |
| **NFR-03** | Local CPU Embedding Inference | $< 20\text{ms}$ embedding generation | `all-MiniLM-L6-v2` with deterministic hash fallback |
| **NFR-04** | Request Body Protection | Maximum 512KB payload | FastAPI `limit_request_body` middleware |
| **NFR-05** | Security & Auth | Constant-time HMAC token comparison | `hmac.compare_digest` in `require_api_token` |
| **NFR-06** | Schema Validation | 100% strict Pydantic v2 schemas | Pure Pydantic models in `models/*` and `api/` |
| **NFR-07** | UI Compositor Performance | 0ms lag / 60fps smooth navigation | Pre-computed CSS gradients + opaque paper glass |

---

## 4. Architecture

### 4.1 System Topology

```text
React 18 Desktop SPA (Port 5173)
  ├── LifeCalendar | JournalView | GoalsView | AICoachView | AnalyticsView | MemoriesView | SettingsView
  └── Axios API Client (frontend/src/api/client.ts)
            │
            ▼ (REST JSON / Port 8000)
FastAPI Application (api/main.py)
  ├── Security: 512KB Body Guard | HMAC Token Validator | CORS
  ├── Coordinator Pipeline (ai/pipelines/coordinator.py)
  │     ├── Intent Triage Engine
  │     ├── Domain-Scoped Toolkits (ai/tools/*)
  │     └── Session Blackboard Bus
  ├── Coaching Orchestration (services/coach_service.py)
  │     ├── 5 Guided Pipelines (Morning, Evening, Weekly, Future Self, Goal Alignment)
  │     └── Deterministic Rule Fallback Engine
  ├── Domain Services
  │     ├── MemoryService (5-Factor Hybrid RAG + MMR)
  │     ├── LifeCalendarService (70-Year Memento Mori)
  │     ├── AnalyticsService & PatternService (Scores & Trends)
  │     ├── ObservabilityService (Telemetry & USD Spend)
  │     └── DataPortabilityService (Export & Safe Reset)
  └── Persistence Layer
        ├── SQLite 3 (goalos.db with FTS5 lexical index)
        └── ChromaDB (chroma_db/ local vector embeddings)
```

### 4.2 Layer Pattern

| Layer | Path | Role |
|-------|------|------|
| Presentation | `frontend/src/` | React 18 + Vite SPA, Forest Mist Paper Glass design |
| API Gateway | `api/main.py` | FastAPI routes, 512KB body limiter, HMAC token security |
| Multi-Agent Coordinator | `ai/pipelines/coordinator.py` | Intent triage, domain toolkits, session blackboard |
| Domain Toolkits | `ai/tools/*` | Function definitions & execution (`journal`, `goals`, `memory`, `calendar`) |
| Coaching Orchestration | `services/coach_service.py`, `ai/pipelines/*` | 5 guided pipelines & local rule fallback engine |
| Domain Services | `services/*` | `MemoryService`, `LifeCalendarService`, `AnalyticsService`, `ObservabilityService`, etc. |
| Repositories | `database/repositories/*` | Data access layer using SQLite context managers |
| Persistence | `goalos.db`, `chroma_db/` | SQLite 3 (relational + FTS5) + ChromaDB (vector cosine index) |

### 4.3 5-Factor Hybrid RAG Memory Flow

$$\text{Composite Score} = 0.35 \cdot S_{\text{sem}} + 0.15 \cdot S_{\text{lex}} + 0.25 \cdot S_{\text{imp}} + 0.15 \cdot S_{\text{rec}} + 0.10 \cdot S_{\text{freq}}$$

1. **Embed** — `all-MiniLM-L6-v2` via `EmbeddingService` (384d vector).
2. **Store** — Dual-write: SQLite `memories` table + SQLite `memory_fts` (FTS5) + ChromaDB collection.
3. **Query** — Combined lexical keyword match ($S_{\text{lex}}$) and ChromaDB cosine distance search ($S_{\text{sem}}$).
4. **Rank** — 5-factor weighting incorporating subjective importance ($S_{\text{imp}}$), 30-day exponential recency decay ($S_{\text{rec}}$), and logarithmic frequency ($S_{\text{freq}}$).
5. **Diversity Prune** — Candidate memories with pairwise cosine similarity $> 0.94$ against already selected memories are pruned via MMR.
6. **Generate** — Injected into coaching context or returned dynamically via agent tool calls.

---

## 5. Data Model

| Store | Tables / Collections | Content |
|-------|---------------------|---------|
| **SQLite (`goalos.db`)** | `user`, `goals`, `milestones`, `daily_logs`, `memories`, `scores`, `coach_sessions`, `coach_messages`, `ai_telemetry`, `settings`, `memory_fts` | Structured relational user data, session state, FTS5 lexical index, and observability telemetry |
| **ChromaDB (`chroma_db/`)** | `memories` collection | Local vector embeddings (384d `all-MiniLM-L6-v2`) for semantic search |
| **Files** | `goalos.db`, `chroma_db/`, `reports/` | Local-first file persistence |

---

## 6. REST API Specification

### Core Endpoints

| Category | Endpoint | Method | Role |
|----------|----------|--------|------|
| **Health** | `/health`, `/api/health`, `/health/details` | `GET` | Service status, database row counts, vector collection stats |
| **Life Calendar** | `/calendar/summary`, `/calendar/grid` | `GET` | Lifespan statistics & 3,640 discrete week blocks |
| **Journal** | `/journal/today`, `/journal/date/{target_date}`, `/journal/history` | `GET` | Fetch daily logs by date or historical limit |
| | `/journal/upsert` | `POST` | Upsert daily log fields & trigger automatic daily score recomputation |
| **Goals** | `/goals`, `/goals/horizons`, `/goals/{id}` | `GET` | Multi-horizon goal queries and horizon grouping |
| | `/goals`, `/goals/{id}` | `POST`, `PUT`, `DELETE` | Goal creation, updates, and cascading deletion |
| | `/goals/{id}/milestones`, `/milestones/{id}` | `POST`, `PUT`, `PATCH`, `DELETE` | Milestone CRUD and completion toggling |
| **Coaching Pipelines**| `/coach/morning`, `/coach/evening`, `/coach/weekly`, `/coach/future-self`, `/coach/goal-alignment` | `POST` | 5 guided structured coaching pipelines with grounded evidence |
| **Coach Chat** | `/coach/chat` | `POST` | Multi-agent conversational coaching (intent routing, scoped tools, blackboard) |
| | `/coach/sessions`, `/coach/sessions/{id}` | `GET`, `POST`, `DELETE` | Chat session creation, history retrieval, and cleanup |
| **Telemetry** | `/coach/telemetry/summary`, `/coach/telemetry/traces` | `GET` | Aggregated latency percentiles (p50/p95) and token/USD spend |
| **Memories** | `/memories`, `/memories/search` | `GET`, `POST`, `DELETE` | 5-factor hybrid RAG search, manual memory addition, and purging |
| **Analytics** | `/analytics/dashboard`, `/analytics/scores` | `GET` | Consolidated averages, behavioral patterns, and historical scores |
| **Settings & Export** | `/settings` | `GET`, `POST` | Profile, life visions, and remote AI consent configuration |
| | `/export`, `/export/reset` | `GET`, `POST` | Full JSON export and safe factory reset with automated backup |

---

## 7. Evaluation & AI Benchmarking

| Metric | Result | Notes |
|--------|--------|-------|
| **pytest Suite** | 106/106 passing (100%) | `pytest -q` across all repositories, services, APIs, and pipelines |
| **AI Evaluation Framework** | 6 GoalOS Vision Metrics | Evaluates Schema Integrity, Grounding, Actionability, Horizon Alignment, Tool Precision, and Operational Efficiency |
| **Free-Tier Model Benchmarking** | 76.8% composite score (`nvidia/nemotron-3-super-120b-a12b:free`) | 45-scenario live evaluation with leaky-bucket rate limiting ($\le 14$ RPM) |
| **Retrieval Evaluation** | `python scripts/generate_retrieval_eval.py` | Generates rubric-based ranking report in `reports/evaluation.md` |

---

## 8. Deployment

| Target | Startup Command / Path |
|--------|------------------------|
| **One-Click Windows Launcher** | `run_app.bat` (boots FastAPI backend on port 8000 and Vite frontend on port 5173) |
| **Manual Backend** | `python -m uvicorn api.main:app --port 8000 --reload` |
| **Manual Frontend** | `cd frontend && npm run dev` |
| **Frontend Production Build** | `cd frontend && npm run build` |

---

## 9. Testing

```powershell
pytest -q
```

Coverage domains:
- Relational schema, migrations, foreign key cascades, and transactional rollbacks.
- 5-factor hybrid memory retrieval, FTS5 sync, and MMR diversity pruning.
- Life Calendar calculations (Memento Mori week indices).
- Guided coaching pipelines, coordinator blackboard state, intent triage, and deterministic fallbacks.
- REST API route contracts, 512KB payload ceiling, and HMAC token authorization.
- AI evaluation framework, rate limiter, and vision metrics.

---

## 10. Architectural Guarantees & Non-Functional Constraints

- **Local-First Data Sovereignty:** All journal entries, active goals, memories, and chat sessions are stored locally in SQLite (`goalos.db`) and ChromaDB (`chroma_db/`).
- **Zero-Surprise Privacy:** Remote LLM execution is disabled by default unless explicitly opted into via `remote_ai_consent` in Settings.
- **Deterministic Rule Fallbacks:** The system functions fully offline with high-utility rule engines returning actionable directives within $< 50\text{ms}$.
- **Safe Operations:** Destructive resets (`/export/reset`) automatically create a timestamped backup of `goalos.db` before data truncation.
- **Payload & Security Protection:** Endpoints enforce a 512KB payload ceiling and constant-time HMAC bearer token authentication.

---

## 11. Module Index

| Path | Purpose |
|------|---------|
| `frontend/src/` | React 18 + TypeScript SPA (7 core views, Forest Mist Paper Glass design) |
| `frontend/src/api/client.ts` | Axios REST client connecting to FastAPI |
| `api/main.py` | FastAPI REST API with CORS, payload limiters, and endpoint routers |
| `ai/pipelines/coordinator.py` | Multi-agent supervisor coordinator with intent triage and blackboard bus |
| `ai/tools/*` | Scoped domain toolkits (`JournalToolkit`, `GoalsToolkit`, `MemoryToolkit`, `CalendarToolkit`) |
| `ai/eval/*` | Production AI evaluation framework, rate limiter, and vision metrics |
| `services/coach_service.py` | Coaching orchestration and deterministic rule fallback engine |
| `services/memory_service.py` | 5-factor hybrid RAG retrieval, dual-write persistence, and MMR diversity |
| `services/life_calendar_service.py` | 70-year lifespan calculation and week grid generation |
| `services/analytics_service.py` | Daily scoring engines (alignment, consistency, health, productivity) |
| `services/pattern_service.py` | Longitudinal multi-day behavioral pattern detection |
| `services/observability_service.py`| AI execution telemetry, latency profiling, and USD token spend tracking |
| `services/data_portability_service.py`| Portable JSON backup and safe factory reset with automated backup |
| `database/migrations.py` | SQLite transactional schema migrations |
| `database/repositories/*` | Data access repositories adhering to SQLite context managers |
