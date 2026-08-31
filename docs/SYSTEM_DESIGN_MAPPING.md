# 🏛️ Production Agentic System Design & Architecture Mapping

---

## 📋 Document Control & Metadata

| Attribute | Specification |
| :--- | :--- |
| **System Name** | GoalOS Executive AI Platform |
| **Architecture Pattern** | Supervisor-Coordinator Multi-Agent Pattern with Domain Toolkits & Blackboard State |
| **Reference Architecture** | Enterprise Banking Agentic AI Design (Zero-Trust, Observability, Session Store, MCP Toolkits) |
| **Implementation Classification** | Local-First, Sovereign, Deterministic Fallback-Enabled |
| **Repository Root** | `C:\Users\jegad\projects\GoalOS` |
| **Document Status** | Approved & Implemented in Production (v2.6.0) |

---

## 1. 🌟 Executive Summary & Architectural Evolution

This document specifies the exact mapping between enterprise-grade production agent architectures (such as banking conversational AI systems) and the **GoalOS Local-First Multi-Agent Architecture**.

GoalOS extracts the core production patterns:
1. **Supervisor Coordinator Agent** for unified intent triage and multi-agent dispatching.
2. **Domain-Partitioned Toolkits** (MCP-ready interface) to eliminate prompt bloat and prevent tool hallucinations.
3. **Persistent Session Store & Blackboard State** for multi-turn conversational history and inter-agent context sharing.
4. **Real-Time Observability & AI Cost Tracker** for trace span profiling, token metering, and live USD spend calculations.
5. **Deterministic Fallback Engine** ensuring 100% operational availability without remote cloud LLM dependencies.

---

## 2. 🗺️ High-Level System Architecture Diagram

```mermaid
flowchart TB
    subgraph Client_Layer ["1. Client Layer (Port 5173)"]
        UI_Chat["React 18 Chat & Coaching Studio"]
        UI_Views["Multi-Horizon Views (Calendar, Goals, Journal, Memories)"]
        UI_Dash["AI Diagnostics & Cost Card"]
    end

    subgraph Edge_Security ["2. Edge & Security Layer (Port 8000)"]
        FastAPI_GW["FastAPI Ingress Gateway"]
        Limit_Guard["512KB Request Body Limiter"]
        Auth_Guard["HMAC Bearer Token Guard (GOALOS_API_TOKEN)"]
        CORS_Guard["CORS & Origin Security Policy"]
        
        FastAPI_GW --> Limit_Guard --> Auth_Guard --> CORS_Guard
    end

    subgraph Coordinator_Layer ["3. Supervisor Coordinator Agent"]
        Coord_Agent["CoordinatorPipeline (ai/pipelines/coordinator.py)"]
        Intent_Classifier["Intent Classifier & Domain Triage Engine"]
        Blackboard_Bus["Inter-Agent Shared Blackboard Context Bus"]
        Synth_Engine["Evidence Grounding & Response Synthesizer"]
        
        Coord_Agent --> Intent_Classifier
        Coord_Agent <--> Blackboard_Bus
        Coord_Agent --> Synth_Engine
    end

    subgraph Domain_Subagents ["4. Specialized Domain Subagents"]
        A_Exec["Execution Coach Agent\n(Morning / Evening / Habit Pacing)"]
        A_Goal["Horizon & Goal Agent\n(1M Sprints / 1Y / 5Y Trajectory)"]
        A_Mem["Cognitive Memory Agent\n(5-Factor Hybrid RAG)"]
        A_Life["Lifespan Awareness Agent\n(70-Year Memento Mori)"]
    end

    subgraph Domain_Toolkits ["5. Domain-Partitioned Toolkits (ai/tools/*)"]
        T_Journal["JournalToolkit\n• get_monthly_progress\n• get_recent_logs"]
        T_Goals["GoalsToolkit\n• get_active_goals\n• get_horizon_pacing"]
        T_Memory["MemoryToolkit\n• search_memories (Hybrid RAG)\n• store_cognitive_insight"]
        T_Calendar["CalendarToolkit\n• get_lifespan_stats"]
    end

    subgraph Model_Gateway ["6. Hybrid Model Gateway (ai/openrouter_client.py)"]
        Remote_LLM["OpenRouter Cloud LLMs\n(Claude 3.5/3.7, Gemini 2.5, Llama 3.3)"]
        Deterministic_Rules["Deterministic Rule Fallback Engine\n(services/coach_service.py)"]
    end

    subgraph Persistence_Layer ["7. Local Persistence & Session Storage"]
        DB_Sessions[("SQLite: coach_sessions\n• session metadata\n• blackboard JSON")]
        DB_Messages[("SQLite: coach_messages\n• role, content\n• tool_calls & citations")]
        DB_Telemetry[("SQLite: ai_telemetry\n• trace spans\n• tokens & USD cost")]
        DB_Core[("SQLite: goalos.db\n• daily_logs, goals, milestones\n• FTS5 memory_fts")]
        Vector_Store[("ChromaDB Vector Store\n• 384d all-MiniLM-L6-v2 embeddings")]
    end

    subgraph Observability_Hub ["8. Observability & APM Hub (services/observability_service.py)"]
        Trace_Engine["Span & Trace Collector"]
        Cost_Tracker["Token Metering & USD Cost Calculator"]
        Latency_Profiler["p50 / p95 Latency Profiler"]
    end

    %% Client to Edge
    UI_Chat -->|HTTP POST /coach/chat| FastAPI_GW
    UI_Views -->|REST CRUD| FastAPI_GW
    UI_Dash -->|GET /coach/telemetry/summary| FastAPI_GW

    %% Edge to Coordinator
    CORS_Guard --> Coord_Agent

    %% Coordinator to Subagents & Toolkits
    Intent_Classifier --> A_Exec & A_Goal & A_Mem & A_Life
    A_Exec --> T_Journal
    A_Goal --> T_Goals
    A_Mem --> T_Memory
    A_Life --> T_Calendar

    %% Toolkits to Persistence
    T_Journal --> DB_Core
    T_Goals --> DB_Core
    T_Calendar --> DB_Core
    T_Memory --> DB_Core & Vector_Store

    %% Coordinator to Sessions & Models
    Coord_Agent <--> DB_Sessions & DB_Messages
    Coord_Agent -->|Remote Consent Active| Remote_LLM
    Coord_Agent -->|Offline / Fallback| Deterministic_Rules

    %% Telemetry flows
    Remote_LLM -.->|Usage & Latency Spans| Trace_Engine
    Trace_Engine --> Cost_Tracker --> Latency_Profiler --> DB_Telemetry
```

---

## 3. 🔄 Multi-Agent Coordination Sequence & Data Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as User (Chat UI)
    participant API as FastAPI Gateway (/coach/chat)
    participant Repo as CoachSessionRepository
    participant Coord as CoordinatorPipeline
    participant Tool as Domain Toolkit Registry
    participant LLM as OpenRouter LLM Gateway
    participant Obs as ObservabilityService
    participant Local as Deterministic Rule Engine

    User->>API: POST /coach/chat {session_id, message: "Pacing on Q3 career goal?"}
    API->>Coord: chat(CoachChatRequest)
    Coord->>Repo: get_session(session_id) / create_session()
    Repo-->>Coord: SessionState (history + active blackboard)
    Coord->>Repo: append_message(role="user", content=message)

    Coord->>Coord: classify_intent(message) -> "goals_pacing"
    Coord->>Tool: get_scoped_tool_definitions(["goals", "memory"])
    Tool-->>Coord: Scoped JSON Function Schemas

    alt Remote AI Consent is Active & API Key Configured
        Coord->>LLM: complete_with_tools(system_prompt, user_prompt, tools)
        LLM->>Tool: Tool Call: get_active_goals()
        Tool-->>LLM: JSON Goals Payload
        LLM-->>Coord: Synthesized Actionable Advice with Goal Evidence
        Coord->>Obs: record_span(model, tokens, latency_ms, cost_usd)
        Obs->>Repo: Save to ai_telemetry
    else Offline / No API Key / Remote Consent Disabled
        Coord->>Local: _run_deterministic_fallback()
        Local-->>Coord: Grounded Rule-Based Advice from SQLite
    end

    Coord->>Repo: update_blackboard(session_id, updated_state)
    Coord->>Repo: append_message(role="assistant", content=reply, tool_calls)
    Coord-->>API: CoachChatResponse
    API-->>User: JSON Response (reply, blackboard, trace_id, latency_ms)
```

---

## 4. 📊 Layer-by-Layer Architectural Mapping Table

| Reference Banking Component | GoalOS Production Component | Implementation Location | Production Responsibility |
| :--- | :--- | :--- | :--- |
| **User Interface (chat)** | Chat Studio & Multi-Horizon Views | `frontend/src/` | Interactive multi-turn coaching, week calendar, daily journal. |
| **Edge Layer (WAF, Rate Limit, API GW)** | FastAPI Security Middleware | `api/main.py` | 512KB payload ceiling, HMAC constant-time auth token guard, CORS validation. |
| **Authentication / IdP** | HMAC Bearer Token Validator | `api/main.py::require_api_token` | Validates API tokens in constant time (`hmac.compare_digest`). |
| **PII & Data Guard** | Local-First Sovereign Persistence | `database/migrations.py` | Zero telemetry or personal data leaves the machine unless explicitly consented. |
| **Coordinator Agent** | Supervisor Coordinator Pipeline | `ai/pipelines/coordinator.py` | Intent classification, domain delegation, response synthesis, and fallback routing. |
| **Accounts / Tx / Service Subagents** | Domain Coach Subagents | `ai/pipelines/*` | `ExecutionCoach`, `GoalAlignmentCoach`, `ProgressCoach`, `FutureSelfCoach`. |
| **Modular MCP Tool Servers** | Domain-Partitioned Toolkits | `ai/tools/*` | `MemoryToolkit`, `GoalsToolkit`, `JournalToolkit`, `CalendarToolkit`. |
| **Session Store & Inter-Agent State** | SQLite Sessions & Blackboard | `database/repositories/coach_session_repository.py` | `coach_sessions` and `coach_messages` with structured JSON blackboard. |
| **LLM Gateway (Hybrid)** | OpenRouter Client + Rule Engine | `ai/openrouter_client.py`, `services/coach_service.py` | Leaky-bucket rate limited cloud models + instant deterministic fallback. |
| **Observability Hub & Cost Tracker** | Telemetry & APM Service | `services/observability_service.py`, `database/repositories/telemetry_repository.py` | Live token tracking, latency percentiles (p50/p95), and USD model spend estimation. |
| **Agent Evaluation Suite** | 6 Vision Metrics Evaluator | `ai/eval/` (`evaluator.py`, `metrics.py`) | JSON integrity, Grounding, Actionability, Horizon Alignment, Tool Precision, Efficiency. |

---

## 5. 🛡️ Architectural Invariants & Guarantees

1. **Context Manager SQLite Transactions:** All persistence MUST use `with get_db() as conn:`.
2. **Deterministic Fallback Invariant:** If remote AI fails or is disabled, the system MUST return high-utility deterministic rules with `source = 'deterministic_rules'`.
3. **Domain Tool Scoping:** Subagents MUST only receive the tool definitions relevant to their domain to conserve prompt tokens and prevent tool hallucinations.
4. **Telemetry Non-Interference:** Telemetry and cost tracking operations MUST be non-blocking and never interrupt core user execution.
