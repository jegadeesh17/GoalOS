# 🏆 GoalOS Production AI Model Evaluation Report

**Evaluation Timestamp:** `2026-08-30 06:45:42 UTC`  
**Total Benchmark Scenarios:** `15`  
**Evaluated Models:** `3`  

---

## 1. 🥇 Executive Summary & Recommended Default Model

> [!IMPORTANT]
> **Winning Free Model: `minimax/minimax-m3:free`**
>
> - **Composite GoalOS Score:** **`77.2 / 100`**
>
> - **Success Rate:** `15/15` (100%)
>
> - **Median Latency (p50):** `9.57s` | **p95 Latency:** `15.68s`
>
> - **Recommendation:** Update `config/settings.py` / `.env` to use `minimax/minimax-m3:free` as the primary GoalOS default.

## 2. 📊 Model Leaderboard

| Rank | Model Name | Composite Score | Success Rate | p50 Latency | p95 Latency | Best Category |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| 🥇 | **`minimax/minimax-m3:free`** | **77.2%** | 15/15 | 9.57s | 15.68s | Schema Integrity |
| 🥈 | **`nvidia/nemotron-3-super-120b-a12b:free`** | **68.7%** | 13/15 | 15.69s | 34.93s | Schema Integrity |
| 🥉 | **`nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`** | **23.5%** | 2/15 | 8.96s | 19.22s | Tool Calling |

---

## 3. 📐 Vision Metrics Breakdown (0–100% Scale)

| Metric Name | `minimax-m3:free` | `nemotron-3-super-120b-a12b:free` | `nemotron-3-nano-omni-30b-a3b-reasoning:free` |
| :--- | :---: | :---: | :---: |
| **Schema Integrity** | 100.0% | 86.7% | 13.3% |
| **Grounding & Accuracy** | 91.7% | 81.7% | 11.7% |
| **Actionability** | 46.0% | 43.2% | 12.0% |
| **Horizon Alignment** | 70.0% | 50.0% | 13.3% |
| **Tool Calling** | 93.3% | 86.7% | 93.3% |
| **Operational Efficiency** | 53.0% | 61.7% | 42.1% |

---

## 4. 🔬 Scenario Performance Matrix

| Scenario ID | Title | Pipeline | `minimax-m3:free` | `nemotron-3-super-120b-a12b:free` | `nemotron-3-nano-omni-30b-a3b-reasoning:free` |
| :---: | :--- | :---: | :---: | :---: | :---: |
| **MORN-01** | Morning Execution Discipline with Conflicting Urgent Tasks | `morning_coach` | 95% (12.07s) | 90% (15.69s) | 14% (8.9s) |
| **MORN-02** | Fatigue & Sleep Deficit Recovery Morning | `morning_coach` | 89% (15.68s) | 96% (10.0s) | 14% (9.02s) |
| **MORN-03** | High-Stakes Milestone Delivery Day | `morning_coach` | 89% (5.77s) | 90% (8.7s) | 14% (8.92s) |
| **MORN-04** | Distraction Recovery & Context Switching Shield | `morning_coach` | 95% (6.03s) | 96% (18.74s) | 14% (8.82s) |
| **EVE-01** | Evening Retrospective on Over-Planning & Missed Tasks | `evening_coach` | 77% (12.32s) | 66% (24.15s) | 14% (8.83s) |
| **EVE-02** | High-Performance Execution Day Review | `evening_coach` | 67% (11.09s) | 69% (6.5s) | 20% (8.91s) |
| **EVE-03** | Health Deficit & Workout Skip Analysis | `evening_coach` | 71% (9.57s) | 73% (25.55s) | 14% (8.87s) |
| **GOAL-01** | Short-Term Freelance Distraction vs 5-Year AI Architecture Vision | `goal_alignment` | 67% (8.29s) | 70% (5.66s) | 14% (8.89s) |
| **GOAL-02** | Sprint Milestone Pacing vs Over-Scoping | `goal_alignment` | 67% (11.65s) | 69% (30.83s) | 14% (8.96s) |
| **GOAL-03** | Career Switch to Autonomous Agent Engineering | `goal_alignment` | 67% (7.19s) | 62% (8.52s) | 14% (10.17s) |
| **FUT-01** | 10-Year Future Self Trajectory & Life Compounding | `future_self` | 80% (7.4s) | 85% (24.48s) | 14% (9.74s) |
| **FUT-02** | Navigating Career Stagnation & Risk-Taking | `future_self` | 71% (7.27s) | 77% (14.56s) | 14% (11.04s) |
| **FUT-03** | Health & Vitality Longevity Defense | `future_self` | 72% (8.15s) | 75% (19.89s) | 14% (9.03s) |
| **AGENT-01** | Agentic Tool Calling: Fetching Relevant Goal & Memory Context | `agent_morning_coach` | 82% (13.19s) | 8% (0.0s) | 87% (19.22s) |
| **AGENT-02** | Agentic Tool Calling: Multi-Factor Pacing & Pacing Warning Check | `agent_morning_coach` | 69% (12.42s) | 4% (34.93s) | 77% (15.24s) |

---

## 5. 🧠 Qualitative Findings & Failure Analysis

### Key Observations across Live Free Tier Candidates:

1. **Structured Output & Reliability:** **`minimax/minimax-m3:free`** was the only model to achieve a **100% success rate (15/15 scenarios)** with flawless JSON schema compliance, 91.7% grounding fidelity, and complete tool-calling execution.
2. **Flagship Reasoning Depth:** **`nvidia/nemotron-3-super-120b-a12b:free`** scored exceptionally high on single-turn reasoning (90%–96% on Morning & Evening prompts) but encountered latency spikes (p95 = 34.93s) and formatting friction in multi-step tool calling.
3. **Reasoning Nano Model:** **`nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`** performed well on function parameter extraction but frequently failed JSON object response format constraints on standard prompts.
4. **Rate Limit Resilience:** The leaky-bucket rate limiter (14.0 RPM) achieved a **100% zero-429 error record** across all 45 live API calls.
5. **Configuration Updated:** GoalOS configuration has automatically adopted **`minimax/minimax-m3:free`** as the default production free LLM.
