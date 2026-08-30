# 🏆 GoalOS Production AI Model Evaluation Report

**Evaluation Timestamp:** `2026-08-30 06:46:49 UTC`  
**Total Benchmark Scenarios:** `15`  
**Evaluated Models:** `3`  

---

## 1. 🥇 Executive Summary & Recommended Default Model

> [!IMPORTANT]
> **Winning Free Model: `nvidia/nemotron-3-super-120b-a12b:free`**
>
> - **Composite GoalOS Score:** **`76.8 / 100`**
>
> - **Success Rate:** `14/15` (93%)
>
> - **Median Latency (p50):** `14.18s` | **p95 Latency:** `40.56s`
>
> - **Recommendation:** Update `config/settings.py` / `.env` to use `nvidia/nemotron-3-super-120b-a12b:free` as the primary GoalOS default.

## 2. 📊 Model Leaderboard

| Rank | Model Name | Composite Score | Success Rate | p50 Latency | p95 Latency | Best Category |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| 🥇 | **`nvidia/nemotron-3-super-120b-a12b:free`** | **76.8%** | 14/15 | 14.18s | 40.56s | Schema Integrity |
| 🥈 | **`minimax/minimax-m3:free`** | **74.4%** | 13/15 | 10.58s | 70.97s | Tool Calling |
| 🥉 | **`nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`** | **22.8%** | 2/15 | 9.03s | 18.75s | Tool Calling |

---

## 3. 📐 Vision Metrics Breakdown (0–100% Scale)

| Metric Name | `nemotron-3-super-120b-a12b:free` | `minimax-m3:free` | `nemotron-3-nano-omni-30b-a3b-reasoning:free` |
| :--- | :---: | :---: | :---: |
| **Schema Integrity** | 94.7% | 88.0% | 13.3% |
| **Grounding & Accuracy** | 93.3% | 91.7% | 11.7% |
| **Actionability** | 49.3% | 49.1% | 10.7% |
| **Horizon Alignment** | 63.3% | 60.0% | 13.3% |
| **Tool Calling** | 93.3% | 93.3% | 86.7% |
| **Operational Efficiency** | 58.6% | 57.4% | 43.7% |

---

## 4. 🔬 Scenario Performance Matrix

| Scenario ID | Title | Pipeline | `nemotron-3-super-120b-a12b:free` | `minimax-m3:free` | `nemotron-3-nano-omni-30b-a3b-reasoning:free` |
| :---: | :--- | :---: | :---: | :---: | :---: |
| **MORN-01** | Morning Execution Discipline with Conflicting Urgent Tasks | `morning_coach` | 96% (18.34s) | 96% (70.97s) | 14% (8.89s) |
| **MORN-02** | Fatigue & Sleep Deficit Recovery Morning | `morning_coach` | 96% (14.18s) | 87% (13.66s) | 14% (8.84s) |
| **MORN-03** | High-Stakes Milestone Delivery Day | `morning_coach` | 96% (11.1s) | 98% (3.95s) | 14% (8.99s) |
| **MORN-04** | Distraction Recovery & Context Switching Shield | `morning_coach` | 96% (25.41s) | 96% (11.12s) | 14% (8.82s) |
| **EVE-01** | Evening Retrospective on Over-Planning & Missed Tasks | `evening_coach` | 75% (8.58s) | 89% (7.87s) | 14% (8.82s) |
| **EVE-02** | High-Performance Execution Day Review | `evening_coach` | 68% (8.64s) | 73% (13.3s) | 20% (8.95s) |
| **EVE-03** | Health Deficit & Workout Skip Analysis | `evening_coach` | 75% (8.78s) | 31% (7.5s) | 14% (9.14s) |
| **GOAL-01** | Short-Term Freelance Distraction vs 5-Year AI Architecture Vision | `goal_alignment` | 62% (7.59s) | 67% (7.75s) | 14% (9.03s) |
| **GOAL-02** | Sprint Milestone Pacing vs Over-Scoping | `goal_alignment` | 69% (7.28s) | 69% (6.58s) | 14% (8.89s) |
| **GOAL-03** | Career Switch to Autonomous Agent Engineering | `goal_alignment` | 62% (21.45s) | 67% (19.41s) | 14% (9.66s) |
| **FUT-01** | 10-Year Future Self Trajectory & Life Compounding | `future_self` | 72% (18.75s) | 72% (13.24s) | 14% (9.3s) |
| **FUT-02** | Navigating Career Stagnation & Risk-Taking | `future_self` | 53% (12.21s) | 85% (21.68s) | 14% (10.68s) |
| **FUT-03** | Health & Vitality Longevity Defense | `future_self` | 80% (17.57s) | 77% (10.58s) | 14% (9.69s) |
| **AGENT-01** | Agentic Tool Calling: Fetching Relevant Goal & Memory Context | `agent_morning_coach` | 82% (40.56s) | 87% (9.81s) | 80% (14.54s) |
| **AGENT-02** | Agentic Tool Calling: Multi-Factor Pacing & Pacing Warning Check | `agent_morning_coach` | 71% (19.18s) | 20% (4.01s) | 72% (18.75s) |

---

## 5. 🧠 Qualitative Findings & Failure Analysis

### Key Observations across Live Free Tier Candidates:

1. **Flagship Reasoning & Grounding Winner:** **`nvidia/nemotron-3-super-120b-a12b:free`** won **1st Place with a 76.8% composite score** and **14/15 (93%) success rate**. It demonstrated superior grounding (93.3%) and flawless morning mentor execution (scoring 96% across all morning scenarios), while successfully completing both multi-turn agentic tool-calling tasks (`search_memories` and `get_performance_summary`).
2. **High-Speed Structured Runner-Up:** **`minimax/minimax-m3:free`** took **2nd Place with a 74.4% composite score** (13/15 success rate), excelling in fast schema formatting and future-self life compounding projections (85% on career risk-taking).
3. **Reasoning Nano Model:** **`nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`** achieved 80%–87% on agentic tool calling, but struggled with single-turn JSON object schema formatting in static pipelines.
4. **Rate Limit Resilience:** The leaky-bucket rate limiter (14.0 RPM) achieved a **100% zero-429 error record** across all 45 live API calls.
5. **Configuration Auto-Applied:** GoalOS `.env` has been set to the top-scoring model:
   ```bash
   OPENROUTER_MODEL=nvidia/nemotron-3-super-120b-a12b:free
   ```
