# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Entries are built from this repository's `feat`, `fix` and `refactor` commit subjects (short hash in parentheses). No version has been released, so everything is under Unreleased.

## [Unreleased]

### Fixed

- `POST /export/reset` called a method that does not exist and returned a 500 `AttributeError`; it now returns 501 with a clear message (`api/main.py`).
- An invalid `date` on `POST /journal/upsert`, `POST /coach/progress` or `POST /coach/future-self` now returns HTTP 400 instead of 500 (`api/main.py`, 3 new tests).
- The coach chat's life-calendar read used attribute access on a dict, so no calendar context was sent on the remote path; it now reads the dict keys (`ai/pipelines/coordinator.py`).
- Two exact floating-point assertions in `tests/test_analytics.py` now use `pytest.approx`.

### Added

- 70-year life calendar and weekly journal sync (`a00742a`).
- Scan of a month-of-journals folder with automatic 4-week batching (`d318ae8`).
- Weekly and monthly journal mentor that maps goals across 1-month, 1-year and 5-year horizons, with local image OCR that needs no API (`052950a`).
- Multi-day behavioral pattern recognition engine (`2e52edb`).
- Journal database alignment, a tabular history view and restored memories (`da9876f`).
- React and TypeScript frontend and an expanded REST API (`1ae963a`).
- `/api/health` alias for the health endpoint (`8cb0d0b`).
- Memories view with a table layout, type filters and a view toggle (`0cba1bb`).
- AI evaluation framework, rate limiter and vision metrics (`86c1313`).
- Multi-agent coordinator with a session blackboard, telemetry and domain toolkits (`92cfa63`).
- Coach chat UI wired to the coordinator, honoring the remote-AI consent setting (`74c61dd`).
- Pipeline-specific coach output and a month review (`50d98df`).
- Import and indexing of September 1-11 journal entries and memories (`8fcf0b3`).
- Default coach model changed to Gemma 4 31B, with automatic failover on timeout (`e6f0e92`).
- Tool-calling benchmark, Pydantic settings and a production spec (`76b9806`).
- Google Cloud Run deployment: multi-stage Dockerfile, `/app` route, demo seed data and a CI/CD workflow (`49051fd`).
- Telemetry dashboard, coach persona tuning, weekly digest and offline PWA support (`7f1dbd3`).
- Demo data seeded automatically on startup with the persona name Alex Chen, plus telemetry and backfilled analytics (`01315c3`).
- Packaged dataset with no personal information (`41b2292`).
- Productivity calendar for the current year with a structured day inspector (`9c56950`).
- Lighter "Forest Mist" visual theme (`7098df8`).
- Journal import normalizes the PLAN section into fixed hourly blocks (`445f0f7`).
- Goals page gets a 10-year horizon, and Settings no longer carries vision fields (`540845d`).
- Day drawer rebuilt around the real six-section journal (`a5eb5c6`).
- Future Self coaching validates pacing toward 5-year and 10-year goals (`e59f535`).
- Fictional demo dataset built through the real import pipeline (`d07bcb3`).
- Monthly snapshots, lever analysis, goal pacing against numeric targets and link-based goal alignment, with `/tasks/review`, `/tasks/links` and `/goals/attention` (`fa141ac`).
- Claude Code Stop hook that enforces an end-of-turn git check (`bcf0c90`).
- A goal's pace can follow the user's own dated expected path (pace points, `/goals/{id}/pace-points`) (`9d191eb`).
- The goal-alignment summary is also returned as one point per fact (`56a3a3d`).

### Changed

- Streamlit entry point moved to `app/app.py` (`855247c`; the Streamlit app was later removed).
- Journal folder preset renamed to a reusable `data/Journal` with dynamic month detection (`f0cdd7d`).
- Monthly performance report standardized into a 3-step format and the codebase cleaned up (`b610dd5`).
- Duplicate metrics removed across the banner, calendar and navbar (`c06a75b`).
- AI Coach pruned to Goal Alignment and Future Self (`3796d6b`).
- Goal records are now the single source of truth for 1-, 5- and 10-year vision (breaking: the free-text vision fields were dropped) (`873a5b8`).
- The real CSV importer now runs through `JournalImportService` (`0d6ae9f`).
- Unreachable coach and weekly-sync code paths removed (`80db208`).
- Documentation refresh: standard doc set (README, docs index, changelog, decisions, license, commented `.env.example`), factual corrections to match the code, and superseded docs archived (this change).

### Fixed

- Pre-page secrets warning removed and `set_page_config` handled safely (`3369f6b`).
- Reserved `PORT` variable removed from the Cloud Run deploy (`1b2880c`).
- Deployment copies `configs/`, sets `PYTHONPATH=/app` and seeds demo data on startup (`c734a10`).
- Missing `pydantic-settings` added to requirements (`22180ff`).
- Local hardcoded journal folder test skipped in CI (`947ec9c`).
- APIRouter mounted at both `/api` and the root so the SPA and older callers both work (`eb3bc78`).
- Coordinator grounding, timeout handling and fallback resilience improved (`c53ef11`).
- Missing geometry elements added to the draw.io architecture diagram (`88a9ff9`).
- Compose healthcheck port drift fixed and scattered environment reads replaced with typed settings (`1539542`).
- Remaining duplicate percentage and count tags removed from the navbar, banner and calendar legend (`cca2d35`).
- Memory Insight filter matches the backend's `journal_insight` type (`e79b132`).
- Memory type is read from the field the API returns (`70ce253`).
- Memory search endpoint no longer calls a nonexistent method (`2d62ead`).
- AWAKE section parsed honestly; the importer no longer fabricates analytics fields (`f6c750e`).
- Task completion markers corrected: a tick means done, a bare X does not (`80bea01`).
- Missing-goal placeholder is no longer quoted as a real goal (`286af40`).
- Compact no-colon PLAN times parsed and sub-hour grid overlap fixed (`635d892`).
- Dead "Deep work" and "Energy" tiles dropped from the frontend (`7b45fc5`).
- Coach no longer guesses age 35 when the birth date is unset (`5f1cd36`).
- Dead "Morning mood" and "Deep work" tiles dropped from Analytics (`04a35e8`).
- Legacy weekly review no longer fed into coaching context (`7497468`).
- Demo data is never loaded outside `ENVIRONMENT=demo` (`74e7b01`).
- Sleep derived from bedtime to wake-up, and task rates read from the task list (`543d631`).
- Stop-hook baseline repairs itself when the SessionStart hook did not run (`cfcfa05`).
- PLAN labeled as an hour-by-hour log and the hours-logged lever reworded (`41e29e3`).
- Hours-logged lever no longer turned into focus advice (`71049e9`).
- Keyword learning score removed, and momentum left unknown without history (`90ef90b`).
- `gap_score` no longer crashes on a goal without `created_at` (`47c9595`).
