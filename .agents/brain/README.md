# 🧠 GoalOS Project Brain — Autonomous Learning & Memory Graph

Welcome to the **GoalOS Project Brain**. This directory serves as the persistent, project-specific cognitive memory layer for Antigravity and AI agents working on the GoalOS codebase.

---

## 🎯 Purpose & Operating Model

The GoalOS Brain enables the AI agent to:
1. **Retain Context Across Sessions:** Never forget past debugging lessons, architectural decisions, and repository invariants.
2. **Execute Autonomously & Safely:** Follow verified system patterns and avoid previously discovered failure modes.
3. **Continuously Evolve:** Automatically record new discoveries, prompt reflections, performance gains, and domain insights after every task.

```
       +-------------------------------------------------------------+
       |                  CONTINUOUS AGENT LEARNING LOOP             |
       +-------------------------------------------------------------+
       |                                                             |
       |  1. READ BRAIN          2. REASON & DECIDE   3. EXECUTE     |
       |  (system_patterns.md    (pair-programming    (type-safe,    |
       |   project_learnings.md)  checkpoints)         verified)     |
       |             │                   │                 │         |
       |             ▼                   ▼                 ▼         |
       |  6. PERSIST KNOWLEDGE   5. EXTRACT LEARNING  4. VERIFY      |
       |  (update_brain.py       (reflect on prompt,  (test suite,   |
       |   evolution_log.md)      gotchas & wins)      lints, runtime|
       |                                                             |
       +-------------------------------------------------------------+
```

---

## 📂 Memory Graph & Repository Topology

| File | Memory Domain | Purpose |
| :--- | :--- | :--- |
| [`system_patterns.md`](./system_patterns.md) | **Invariants & Conventions** | Code standards, SQLite connection patterns, Pydantic schemas, React hooks, Tailwind design system tokens. |
| [`project_learnings.md`](./project_learnings.md) | **Accumulated Learnings** | Hard-won insights, bug fixes, edge case discoveries, performance optimizations, and library nuances. |
| [`architectural_decisions.md`](./architectural_decisions.md) | **ADRs** | Architecture Decision Records capturing the rationale, trade-offs, and historical context of major design choices. |
| [`troubleshooting_kb.md`](./troubleshooting_kb.md) | **Diagnostics & Playbooks** | Quick-reference runbooks for known error modes (ChromaDB lockups, FTS5 sync, Windows PowerShell quirks, Vite dev proxy). |
| [`active_context.md`](./active_context.md) | **State of the Project** | Active focus areas, current roadmap sprints, completed milestones, and immediate next steps. |
| [`evolution_log.md`](./evolution_log.md) | **Agent Evolution Log** | Chronological log of prompts, actions taken, verifications performed, and self-reflections. |
| [`update_brain.py`](./update_brain.py) | **Automation CLI** | Python automation tool for logging prompt reflections, updating knowledge banks, and searching memory. |

---

## 🛠️ Automated Memory Operations

The agent or developer can interact with the brain programmatically via `update_brain.py`:

```bash
# Append a new project learning
python .agents/brain/update_brain.py --add-learning --domain "memory_service" --summary "MMR Diversity Threshold" --details "Threshold at 0.94 prevents redundant reflections."

# Record a prompt reflection in the evolution log
python .agents/brain/update_brain.py --log-evolution --action "Added Goal Horizon Filter" --reflection "Ensured database index is used for status+horizon queries."

# Search existing brain knowledge
python .agents/brain/update_brain.py --query "ChromaDB connection"
```

---

## 📜 Agent Guidelines for Brain Maintenance

1. **Before Any Non-Trivial Task:** Consult `system_patterns.md` and `project_learnings.md` to ensure design consistency.
2. **During Implementation:** Avoid repeating past anti-patterns listed in `troubleshooting_kb.md`.
3. **After Every Prompt Execution:** If a new edge case was discovered, fixed, or verified, append the lesson to `project_learnings.md` and log the summary to `evolution_log.md`.
