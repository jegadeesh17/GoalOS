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
| **P95 Latency Budget** | < 2,500 ms (End-to-End LLM Tool Loop) | Domain-scoped toolkits minimize schema tokens; local ChromaDB embeddings run in < 80ms. |
| **Payload Ceiling** | 512 KB max request body | Enforced via FastAPI middleware to prevent memory DOS. |
| **Configuration** | Pydantic Settings (`configs/settings.py`) | Typed environment validation; zero scattered `os.environ.get()` calls. |
| **Tool Calling Contract** | Strict Function Calling JSON Schemas | Pydantic validation on tool arguments with graceful rejection of unauthorized tools. |
| **Persistence Layer** | Dual-write SQLite + ChromaDB | SQLite maintains ACID entity state; ChromaDB maintains dense vector embeddings. |
| **Test Coverage** | 109 automated unit/integration tests | 100% of repositories, services, and endpoints covered with mocked external LLM calls. |

---

## 3. Deployment & Containerization
- Multi-stage Docker build with non-root user (`appuser`).
- Automated container healthcheck: `HEALTHCHECK --interval=30s CMD curl -f http://localhost:8000/health || exit 1`.
- Orchestrated via `docker-compose.yml` (FastAPI REST API on port 8000 + Streamlit on port 8501).
