# GoalOS — Production Specification & Contracts

> **Compliance**: Conforms to [`PRODUCTION_ENGINEERING_STANDARDS.md`](file:///C:/Users/jegad/projects/ZGeneral/reference/PRODUCTION_ENGINEERING_STANDARDS.md)  
> **Full Architecture & Spec**: [PROJECT_SPEC.md](file:///C:/Users/jegad/projects/GoalOS/docs/PROJECT_SPEC.md) & [ARCHITECTURE_AND_SPECIFICATIONS.md](file:///C:/Users/jegad/projects/GoalOS/docs/ARCHITECTURE_AND_SPECIFICATIONS.md)

---

## 1. System Overview & Problem Statement
GoalOS is an agentic executive life operating system that combines structured state tracking with continuous cognitive memory and autonomous AI coaching. Unlike generic chatbots or static todo apps, GoalOS actively synthesizes multi-day journal insights, retrieves contextual memories via 5-factor composite ranking, and invokes domain-partitioned toolkits (`memory`, `goals`, `journal`, `calendar`) through strict function-calling contracts.

---

## 2. Technical Contracts & Performance Budgets

| Dimension | Production Standard / Budget | Production Defense |
| :--- | :--- | :--- |
| **Tool-Routing Latency (P95, warm)** | ~54 ms per tool call, warm state† | Domain-scoped toolkits minimize schema tokens; local ChromaDB embeddings run in < 80ms once warm. |
| **Payload Ceiling** | 512 KB max request body | Enforced via FastAPI middleware to prevent memory DOS. |
| **Configuration** | Pydantic Settings (`configs/settings.py`) is the single source of truth for env access | Typed environment validation everywhere; the one intentional exception is an explicit `reload_settings()` path used by the Settings page to pick up a freshly-saved `.env` without restarting the process. |
| **Tool Calling Contract** | Strict Function Calling JSON Schemas | Pydantic validation on tool arguments with graceful rejection of unauthorized tools. |
| **Persistence Layer** | Dual-write SQLite + ChromaDB | SQLite maintains ACID entity state; ChromaDB maintains dense vector embeddings. |
| **Test Coverage** | 126 automated unit/integration tests (verified via `pytest`) | 100% of repositories, services, and endpoints covered with mocked external LLM calls. |

† Measured by running `scripts/benchmark_tool_calling.py`'s benchmark 30 times in a single warm process (203 warm-state tool-call samples after the first run): P95 ≈ 54 ms, P99 ≈ 57 ms. This benchmark exercises local tool-routing/registry dispatch plus SQLite/ChromaDB I/O only — it does **not** make a real OpenRouter network call, so it is not a measurement of full end-to-end LLM tool-loop latency, and no such number has been benchmarked against a live model. Treat any "End-to-End LLM Tool Loop" latency figure as unverified until it is. The checked-in single-run sample in `reports/tool_calling_benchmark.json` (n=7) reports a P95 of ~25–29 seconds; that is not steady-state latency, it is a one-time embedding-model weight-load cost paid by `search_memories`'s first call in a fresh process (confirmed by re-running in-process: every subsequent call drops to low double-digit milliseconds). That cold-start cost is paid once per process lifetime (e.g. once per Cloud Run instance/revision), not per request.

---

## 3. Deployment & Containerization
- Multi-stage Docker build with non-root user (`appuser`).
- Automated container healthcheck: `HEALTHCHECK --interval=30s CMD curl -f http://localhost:${PORT:-8080}/health || exit 1`, so it always probes whatever port the app actually bound (Cloud Run injects `PORT=8080` by default; local `docker compose` sets `PORT=8000`).
- Orchestrated via `docker-compose.yml` (FastAPI REST API on port 8000 + Streamlit on port 8501); the `api` service sets `PORT=8000` via `environment:` rather than overriding the container's start command, so the healthcheck and the running server always agree on the port.
