# 🏛️ Architecture Decision Records (ADRs)

This document tracks the consequential architectural decisions made in GoalOS, documenting the context, alternatives considered, decision rationale, and consequences.

---

## ADR-001: SQLite 3 + ChromaDB Dual-Write Persistence

### Status
**Accepted**

### Context
GoalOS requires structured relational querying (goals, daily logs, milestones, analytics scores) as well as vector similarity search for semantic memory retrieval. Using a single vector database for all structured data adds operational complexity, while SQLite alone lacks efficient vector distance indexing without third-party extensions.

### Decision
Implement a dual-write architecture:
1. **SQLite 3** (`goalos.db`) is the primary source of truth for all structured data, user profiles, and full-text lexical search via SQLite FTS5.
2. **ChromaDB** (`chroma_db/`) acts as a dedicated vector index for memory embeddings.
3. If ChromaDB indexing fails or becomes desynchronized, SQLite marks the memory as `index_status = 'pending'`, and `MemoryService.reconcile_index()` can re-index all active rows from SQLite.

### Consequences
- **Pros:** Zero-dependency local setup, full SQL query capabilities, crash-resilient vector recovery, local-first privacy.
- **Cons:** Requires two write operations per memory; requires reconciliation logic if vector database files are deleted.

---

## ADR-002: Migration from Streamlit to React 18 + TypeScript + Vite

### Status
**Accepted**

### Context
GoalOS originally used Streamlit for rapid prototyping. However, Streamlit's full-page re-run execution model caused latency and visual flickering when interacting with the 3,640-week Life Calendar and complex multi-horizon goal checklists.

### Decision
Migrate the primary UI to a modern single-page application built with **React 18, TypeScript, Vite, and Tailwind CSS**, communicating with a **FastAPI** backend via typed REST endpoints.

### Consequences
- **Pros:** Sub-millisecond UI interactions, smooth animations, customizable celestial light design system, clear separation between frontend and backend.
- **Cons:** Requires running two processes (Vite dev server on 5173 + FastAPI on 8000), which is automated via `run_app.bat`.

---

## ADR-003: Deterministic Rule Engines for Zero-Key & Offline Fallback

### Status
**Accepted**

### Context
Users may run GoalOS offline, without configuring an `OPENROUTER_API_KEY`, or with `remote_ai_consent` set to `False`. The application must remain fully functional and insightful even without remote LLM APIs.

### Decision
Implement deterministic coaching rule engines in `services/coach_service.py` and `services/pattern_service.py`. When remote LLM execution is unavailable or declined, the service synthesizes mentor guidance from local behavioral heuristics, score trends, and active goal milestones.

### Consequences
- **Pros:** 100% offline reliability, guaranteed response within milliseconds, zero recurring API cost for basic usage.
- **Cons:** Fallback guidance lacks the conversational natural language nuance of large language models, but provides structured, actionable directives.

---

## ADR-004: 5-Factor Composite Memory Ranking Formula

### Status
**Accepted**

### Context
Pure cosine similarity search often retrieves semantically similar but outdated or trivial memories while ignoring critical user lessons or recently logged commitments.

### Decision
Adopt a composite scoring formula that weights 5 independent signals:
1. **Semantic Similarity ($35\%$)**: Cosine similarity against query vector.
2. **Lexical Match ($15\%$)**: Exact keyword presence via SQLite FTS5.
3. **User Importance ($25\%$)**: Subjective importance rating assigned by the user.
4. **Recency Decay ($15\%$)**: Exponential decay with a 30-day half-life.
5. **Access Frequency ($10\%$)**: Logarithmic frequency score favoring proven insights.

### Consequences
- **Pros:** Balanced, highly relevant cognitive retrieval that favors important and recently relevant insights.
- **Cons:** Requires tuning weights and logging memory access events.

---

## ADR-005: Supervisor-Coordinator Multi-Agent Pattern with Domain Toolkits & Blackboard State

### Status
**Accepted**

### Context
As coaching capabilities grew (morning planning, evening retrospectives, weekly reviews, multi-horizon goal pacing, and cognitive memory search), passing all tool definitions simultaneously into every conversational turn bloated prompt tokens by 40-50% and caused occasional tool hallucination or out-of-domain tool calls. Furthermore, multi-turn conversations needed state persistence and telemetry across turns without relying on external SaaS databases.

### Decision
Implement a Supervisor-Coordinator architecture modeled on enterprise-grade agent designs:
1. **Coordinator Agent (`ai/pipelines/coordinator.py`):** Acts as the supervisor that classifies user conversational intent into domains (`execution`, `goals`, `memory`, `calendar`, `general`).
2. **Domain-Scoped Toolkits (`ai/tools/*`):** Partition tool definitions into discrete modules (`JournalToolkit`, `GoalsToolkit`, `MemoryToolkit`, `CalendarToolkit`). The coordinator injects only domain-relevant tools into each prompt.
3. **Session Store & Blackboard State (`database/repositories/coach_session_repository.py`):** Persists multi-turn conversations in SQLite tables `coach_sessions` and `coach_messages`, retaining an inter-agent JSON `blackboard` bus.
4. **Non-Blocking Telemetry & APM Hub (`services/observability_service.py`):** Spans, token consumption, and estimated USD spend are asynchronously recorded to table `ai_telemetry` without impacting user latency.
5. **Deterministic Fallback Engine:** Guarantees instant, structured responses from local heuristics when offline or when remote AI consent is turned off.

### Consequences
- **Pros:** 40-50% prompt token reduction, zero out-of-domain tool hallucinations, stateful multi-turn coaching sessions, live USD spend observability, and guaranteed offline availability.
- **Cons:** Requires schema migration for session and telemetry tables and maintaining domain toolkit mappings.

---

## ADR-006: Canonical /api Dual Mount & Route Normalization

### Status
**Accepted**

### Context
In local development, Vite proxied `/api` requests to FastAPI while stripping the `/api` prefix, masking a routing mismatch. In production on GCP Cloud Run, FastAPI directly serves the compiled React single-page application at `/app`. The React Axios client (`frontend/src/api/client.ts`) initiates all network requests with `baseURL: '/api'`, causing all production API calls (`/api/calendar/summary`, `/api/settings`, etc.) to return HTTP 404 Not Found.

### Decision
1. Refactor all FastAPI endpoints into an `APIRouter` (`api_router`).
2. Mount `api_router` canonically at `prefix="/api"` (documented in OpenAPI / Swagger schema).
3. Mount `api_router` simultaneously at root `prefix=""` with `include_in_schema=False` to preserve backward compatibility for direct test suites, scripts, and legacy callers.
4. Normalize `frontend/vite.config.ts` proxy to preserve the `/api` path in local development.

### Consequences
- **Pros:** Completely fixes production SPA data loading, prevents test suite regressions, avoids OpenAPI schema duplication, and aligns local development routing with production Cloud Run routing.
- **Cons:** Requires endpoints to be registered via router instead of directly on `app`.

