# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

GoalOS is a single-user, local-first life OS: a FastAPI backend (SQLite + ChromaDB), a React/Vite/Tailwind SPA, and AI coaching via OpenRouter with a deterministic rule-engine fallback. `AGENTS.md` and `.agents/brain/` (local only, not tracked in the repo) hold the project's own agent rules and accumulated lessons (`system_patterns.md` lists invariants, `project_learnings.md` the past bugs); read them before designing anything non-trivial. `AGENTS.md` also sets the git workflow (atomic Conventional Commits, stage files by name, never `git add -A`), which differs from a "commit only when asked" default.

## Commands

Run from the repo root with the project `.venv` activated (no `.venv` is checked in; create one with `python -m venv .venv && pip install -r requirements-dev.txt`).

```bash
python -m uvicorn api.main:app --port 8000 --reload   # backend (docs at /docs)
cd frontend && npm install && npm run dev             # frontend on :5173, proxies /api -> :8000
run_app.bat                                           # Windows: launches both

pytest -q                                             # full suite (CI runs this)
pytest tests/test_journal_import.py::test_name -q     # single test
ruff check .                                          # lint (line length 120)
mypy api ai config database models services --no-error-summary   # same scope as CI
cd frontend && npm run build                          # tsc typecheck + vite build (no JS test runner exists)

python scripts/generate_retrieval_eval.py             # CI also runs this
docker build .                                        # CI also runs this
```

CI (`.github/workflows/ci.yml`) runs pytest, ruff, mypy, the retrieval eval script and a docker build on Python 3.11, so keep code 3.11-compatible even though local is 3.13.

## Architecture

**Layering (enforced by convention, see `.agents/brain/system_patterns.md`, local only):** `api/main.py` (one ~830-line file, a single `api_router`) → `services/` → `database/repositories/` → SQLite/Chroma. Routes must not run raw SQL. `models/` are pure Pydantic v2 schemas. Note the existing code in `api/main.py` is an exception: `_get_user_calendar_service` runs a query inline.

- **SQLite:** always `with get_db() as conn:` (`database/connection.py`; commits on exit, rolls back on error, `sqlite3.Row`). Schema changes go only through the numbered `MIGRATIONS` list in `database/migrations.py`, run at startup. Don't nest `get_db()` blocks or call a service that opens its own write transaction from inside one; on Windows this hangs (pre-fetch reads, close, then call the service).
- **Settings:** `configs/settings.py` is the real implementation; `config/settings.py` re-exports it and is the preferred import. `reload_settings()` mutates the singleton in place so `.env` edits are picked up without restart. Tests monkeypatch `settings.settings.DB_PATH`/`CHROMA_PATH`.
- **Memory (hybrid RAG):** `MemoryService.store()` dual-writes SQLite `memories` + FTS5 `memory_fts`, then tries Chroma; if Chroma is locked it sets `index_status='pending'` instead of failing. Chroma paths must be canonicalized (`Path.resolve()`) and clients cached in `services/memory_service.py`. Retrieval is a fixed 5-factor weighted score with MMR dedupe at cosine > 0.94 (weights in `system_patterns.md` §3.1). `EmbeddingService` falls back to hash embeddings if `sentence-transformers` is missing.
- **AI coaching:** `ai/pipelines/coordinator.py` (`CoordinatorPipeline.chat`) classifies intent by keyword rules into a domain, reads that domain's data itself (the same reads the `ai/tools/registry.py` toolkits expose) and pastes it into one `OpenRouterClient.complete` call with no `tools` argument, so the model never chooses tools (`complete_with_tools` is only used by tests), and persists multi-turn state in `coach_sessions`/`coach_messages` with a `blackboard` JSON. `progress_coach.py` (Goal Alignment) and `future_self_coach.py` are single-shot pipelines; prompts live in `ai/prompts/*.txt`. `OpenRouterClient` rotates models on timeout/5xx. Every LLM call logs latency/tokens/cost to `ai_telemetry` via `ObservabilityService`.
- **Deterministic fallback is mandatory:** if `remote_ai_consent` is false (key/value `settings` table via `SettingsService`, off by default), `OPENROUTER_API_KEY` is empty, or the network fails, return rule-engine output with `fallback_reason`: the guided pipelines use `fallback_progress` / `fallback_future_self` in `ai/pipelines/_base.py` (`source='heuristic_fallback'`), and the chat coordinator uses `_run_deterministic_fallback` in `ai/pipelines/coordinator.py` (`source='deterministic_rules'`). A consent flag must be traced from storage to every call site; a backend default of `True` once overrode the user's setting.
- **Monthly analytics and goal pacing:** `services/monthly_analytics_service.py` rebuilds one stored snapshot per month (`monthly_snapshots`) from `daily_logs` and `scores`; facts are recomputed on every journal save (`with_insights=False`), levers (`services/monthly_levers.py`, Spearman + seeded permutation test, Bonferroni-corrected tiers) on import/backfill or `POST /analytics/monthly/recompute`. A month is `final` only when it has ended and the last logged day is its last day. `monthly_goal_results` freezes each goal's state for the month (written only while current/previous and not final). Goals may carry a numeric target (`metric_name`, `metric_unit`, `start_value`, `target_value`); `YearlyPacingService` judges pace from the user's monthly check-ins (`goal_measurements`) and reports `qualitative` / `no_check_ins` / `baseline_only` instead of inventing progress. Expected pace is a straight line from start to target unless the user wrote their own dated values for the goal (`goal_pace_points`, API `/goals/{id}/pace-points`, not to be confused with goal milestones); then it follows those points joined by straight lines, the on-pace band scales to the segment, the result carries `path: "custom"`, and the trend projection is left out. The coach context (`monthly_history`, `goal_pacing`) and the tools `get_monthly_snapshots` / `get_goal_pacing` read the same data.
- **Goal alignment and consistency:** alignment is the share of completed, *reviewed* tasks in a 14-day window that serve a goal. `services/task_link_service.py` resolves a task by `task_key` in order: explicit link (`task_links`, kind `goal` or `none`), then a unique match on the goal's user-written `cues` (token-prefix), else unreviewed, which is excluded (never "misaligned"). Fewer than 5 reviewed tasks gives `None`. Consistency is the share of logged days with at least half the tasks ticked, 70/30 with wake-time regularity (`None` under 7 logged days). Changing a link or cue calls `recompute_all_scores()`; a journal save re-scores from that day on. Both scores may be `None` and are left out of the overall.
- **Task rates:** `daily_logs.task_completion_rate` is a percent from the import script but a 0-1 fraction from the Journal editor, so derive rates from `planned_tasks` (`journal_helpers.planned_task_rate`), never the stored column. Sleep for a day is yesterday's bedtime to today's wake time (`JournalImportService.sleep_between`), recomputed whenever entries are imported.
- **Frontend:** `frontend/src/api/client.ts` is the only HTTP client (45s timeout). Journal autosave uses refs + a 1.2s debounce and an IndexedDB offline queue (`offline/journalStash.ts`); use `lib/date.ts` for dates, never `toISOString().split('T')[0]` (UTC off-by-one in IST). `vite-plugin-pwa` is configured so FastAPI serves the built SPA at `/app` and bundles at `/assets` (`frontend/dist` must exist for the root redirect).
- **Design system ("Forest Mist Paper Glass"):** Plus Jakarta Sans for UI, Newsreader (`font-serif` / `.voice`) for time and the user's own words; sentence-case labels, no uppercase eyebrows, no nested cards, no repeated metrics, motion only in response to actions. Tailwind 3 silently drops unsupported values (`bg-white/86`, `ring-3`, `shadow-xs`, ...); use scale values or bracket syntax and grep the compiled CSS to confirm a class exists. Full token list in `system_patterns.md` §2.

## Data & privacy rules (important)

- **This repo is public; the user's real journal is not.** `goalos.db`, `chroma_db/`, `backups/`, `data/Journal/`, `data/journal_*` and `*.csv` (except `data/demo_seed.csv`) are gitignored, and `.gitignore` alone proves nothing: check `git ls-files`. The real journal was once leaked via force-added files and purged from history. Never derive demo data from real data, never read or edit `.env`, and never commit anything generated from the real DB (reports, exports).
- **Demo data is fictional by construction.** `ENVIRONMENT=demo` (Cloud Run) makes `services/demo_seeder.py` copy `data/demo_goalos.db` + `data/demo_chroma_db/` into place at startup; it is a no-op in any other environment. Regenerate with `python scripts/generate_demo_journal.py data/demo_seed.csv` then `python scripts/build_demo_db.py`.
- **Never guess data.** A missing/unparseable value stays `NULL`/empty; no default constants or estimates in importers, backfills or analytics (the old backfill script invented sleep/mood values and contaminated scores). Before any script touches the real `goalos.db`, take a backup with `DataPortabilityService.create_backup()` and verify results with a read-only query afterwards.
- **Journal import:** the user bulk-imports transcribed paper notebooks (weekly/biweekly); they do not journal live in the app. The real pipeline is `scripts/import_journal_csv.py`, which delegates PLAN/TASKS/AWAKE parsing to `services/journal_import_service.py`; verify parsing changes against real data, not just test fixtures. Task done-marks are tick/✓/✔/`[done]`; a bare "X" means *not* done. Features must work with batch-cadence data (no "run daily" flows).
- **Tests must never touch the live DB:** use the `temp_db` fixture from `tests/conftest.py`.

## Deployment & branches

`main` auto-deploys to Google Cloud Run via `.github/workflows/deploy.yml` (also triggers on `feat/coach-chat-ui`) with `ENVIRONMENT=demo`; the multi-stage `Dockerfile` bakes in the demo DB, not the real one. Do day-to-day work on `dev` and don't merge to `main` without explicit sign-off. With `ENVIRONMENT=production` the API refuses to start without `GOALOS_API_TOKEN`; the bearer check is `require_api_token` (empty token means open local mode), and request bodies are capped at 512KB.

## Style

Existing Python files mix 2-space (`api/`, `database/`, `tests/`) and 4-space (`configs/`, `services/demo_seeder.py`, `scripts/`) indentation; match the file you are editing. Ruff selects `E,F,I,B`; mypy runs with `check_untyped_defs`. When removing a feature, `git grep` its route, service method, prompt and UI label across code and `README.md`/`docs/` and update them in the same change.
