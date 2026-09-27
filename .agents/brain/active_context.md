# 📍 GoalOS Active Context & Operational Roadmap

> Last refreshed: 2026-09-28 (codebase audit).

This document outlines the current project status, active features, technical health, and near-term enhancement roadmaps.

---

## 1. 📊 Project Status & Vital Metrics

| Metric | Status / Value | Notes |
| :--- | :--- | :--- |
| **System Architecture** | ✅ Modern React + FastAPI | Single-page application backed by FastAPI 2.1 |
| **Persistence Engine** | ✅ SQLite 3 + ChromaDB | Dual-write vector indexing and FTS5 search operational |
| **AI Coaching Suite** | ✅ 2 Pipelines + Multi-Agent Coordinator | Goal Alignment (`progress_coach.py`, `/coach/progress`, monthly/yearly pacing) and Future Self (`future_self_coach.py`, 5/10-year pacing), plus `CoordinatorPipeline` free-form chat. Morning/Evening/Weekly/Reflection were removed (2026-09-27/28) because the user bulk-imports, never journals daily |
| **Coach Chat UI** | ✅ Wired end-to-end | Sessions sidebar + chat thread in `AICoachView.tsx`; pipeline-specific fields render directly instead of a generic fallback line |
| **Test Suite** | ✅ 161/161 Passing Tests (2026-09-28) | `pytest -q`; `ruff check .` and `tsc --noEmit` clean |
| **Design System** | ✅ Forest Mist Paper Glass | Opaque emerald/sage glass panels, static pre-computed gradient washes, Plus Jakarta Sans + Newsreader typography |
| **Journal Data** | ✅ 2026-07-01 → 2026-09-11 (73 days) | Six-section notebook (Gratitude, Awake, Plan, Tasks, Review, Takeaway) transcribed to `data/Journal/journal_data.csv` and imported via `scripts/import_journal_csv.py`, which delegates parsing to `JournalImportService`. Pre-July data deleted 2026-09-27; AWAKE backfilled 2026-09-28 (habit starts Aug 3) |

---

## 2. 🎯 Active Sprints & Enhancements

### Sprint 1: Architecture Formalization & Autonomous Memory (Current)
- [x] Complete High-Level Architecture & Technical Specification Document (`docs/ARCHITECTURE_AND_SPECIFICATIONS.md`).
- [x] Establish Project-Specific Brain structure (`.agents/brain/`).
- [x] Create Agent Rules for continuous self-improvement and high performance.
- [x] Build automated Brain CLI utility (`.agents/brain/update_brain.py`).

### Sprint 2: Multi-Agent Coordinator, Chat UI & Grounding (Current)
- [x] Implement production `CoordinatorPipeline` with intent classification, scoped toolkits, session blackboard, and telemetry (`ai/pipelines/coordinator.py`, `database/repositories/{coach_session,telemetry}_repository.py`).
- [x] Wire `AICoachView.tsx` chat UI to `/coach/chat` + sessions CRUD; respect the saved `remote_ai_consent` setting on every chat send (previously defaulted to `True` regardless of the Settings toggle).
- [x] Fix `AICoachView` rendering only a hardcoded directive (`mentor_rule`/`rule`/`core_insight`/`coaching`) for every pipeline — now renders each pipeline's real fields (future-self `message`, goal-alignment `alignment_narrative`/`aligned_goals`/`neglected_goals`) and only falls back when a pipeline truly returns nothing.
- [x] Ingest the remaining August 2026 journal days (16–31) so coaching pipelines are grounded on the full month, not just the first half.

### Sprint 3: Route Prefix Normalization & Cloud Run Alignment (Completed Sept 16, 2026)
- [x] Debug live Cloud Run instance (`https://goalos-api-242711953247.asia-south1.run.app/app`) 404 API loading errors.
- [x] Transition FastAPI surface in `api/main.py` to `api_router` with dual mounting (`prefix="/api"` canonical and `prefix=""` legacy alias).
- [x] Remove path rewrite in `frontend/vite.config.ts` so development and production environments behave identically.
- [x] Add dual-route test assertions in `tests/test_api.py` and `tests/test_api_expansion.py` (100% tests passing).
- [x] Compile master `implementation_plan.md` documenting current state, ADR-006, and future roadmap.

### Sprint 4: Extended AI Coach Observability & Telemetry Surface (Upcoming)
- [ ] Implement live latency and cost dashboard in React frontend consuming `/api/coach/telemetry/summary` and `/api/coach/telemetry/traces`.
- [ ] Add interactive prompt playground in Settings for custom coaching persona prompts.

---

## 3. 🧩 Key Component Locations

- **FastAPI Surface:** `api/main.py`
- **React Frontend Source:** `frontend/src/`
- **Hybrid RAG Service:** `services/memory_service.py`
- **Coaching Orchestrator:** `services/coach_service.py`
- **Database Migrations:** `database/migrations.py`
- **System Specifications:** `docs/ARCHITECTURE_AND_SPECIFICATIONS.md`
- **Project Brain:** `.agents/brain/`
