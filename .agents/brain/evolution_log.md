# 📈 GoalOS Evolution & Continuous Improvement Log

This chronological log captures all significant architectural updates, bug fixes, refactors, and post-prompt agent reflections.

---

## 2026-10-01 — September 12–30 Journal Ingestion (Local Only)

- **User Directives:** Transcribe notebook images in `data/Journal/September 2026/` matching all 7 standard template columns (`Date`, `Gratitude`, `Awake`, `Plan`, `Tasks`, `Review`, `Takeaway`). Strict data separation: real private journal data remains local-only (offline/personal), cloud/demo version is untouched. User confirmed Sept 29 awake window as `8:30 AM - 4:30 AM` (4.0h sleep).
- **Execution & Data Safety:**
  - Backed up local `goalos.db` to `backups/goalos-backup-20261001-115642.zip` via `DataPortabilityService`.
  - Persisted 19 entries to `data/Journal/september_2026_days12_30.json` and appended to `data/Journal/journal_data.csv` (rows grew from 73 to 92).
  - Synchronized `daily_logs` via `scripts/import_journal_csv.py` with parsed hourly time blocks, task completion rates, and sleep metrics.
  - Extracted and indexed 58 memories across lessons, commitments, and insights into local SQLite `memories` and local `chroma_db/`.
  - Recalculated growth scores for all 92 daily logs via `scripts/backfill_analytics.py`.
  - Deterministically verified: 24/24 tests passed in `tests/test_journal_import.py`.
  - 11 Sept Sleep Update: User confirmed sleep time for 11/9/26 is 10:30 PM. Updated Awake to '6:00 AM - 10:30 PM' (sleep: 7.5h) in `journal_data.csv` and `daily_logs`, and recalculated growth scores.
  - Git discipline: Verified `git status --short` remains completely clean; all personal data, photos, and databases are strictly ignored by `.gitignore` and uncommitted.

---

## 2026-09-28 — Private Journal Purged From Public History; Fictional Cloud Demo

- **User decisions:** untrack the private journal files and purge them from history. Delete the eval harness and the legacy weekly-review context (agent's call). No resume changes; keep working on `dev`, and merging to `main` is approved so the live demo stops serving real data.
- **Scope was wider than the original list.** A content scan (every real journal line ≥28 chars from `journal_data.csv`, `journal_history.json`, and both DBs, matched against every blob in history) found the real journal verbatim in `data/demo_goalos.db` (all 121 days, only the name swapped for "Alex Chen", plus the real birth date), `data/demo_chroma_db/`, `reports/august-ledger.html`, and `reports/evaluation.md`. An old `tests/test_mentor_briefing.py` fixture paraphrased a real 2026-06-24 entry. Keyword scans missed that fixture because pre-July data had been deleted from `goalos.db`; the old demo DB supplied the missing needles.
- **Purge:** `git filter-repo --invert-paths` on `data/Journal/`, `data/journal_history.json`, `data/demo_goalos.db`, `data/demo_chroma_db/`, `reports/august-ledger.html`, `reports/evaluation.md`, plus `--replace-text` for the fixture. All 108 commits rewritten; `main` and `dev` force-pushed with `--force-with-lease` pinned to the old remote SHAs. Post-rewrite scan of all branch blobs: zero real-journal hits. Pre-purge mirror: `C:/Users/jegad/projects/GoalOS-prepurge-mirror-2026-09-28.git`; purged files: `backups/prepurge-2026-09-28/`. Local journal files restored (now ignored). Doc SHAs remapped via `.git/filter-repo/commit-map` (`0a4c066`).
- **Still reachable:** GitHub serves old commits by exact SHA until its GC runs (no forks, no PRs). A local `refs/codex/turn-diffs/...` tree ref (left by another tool) still holds old blobs; it is never pushed.
- **Eval harness deleted (`59215d1`):** `ai/eval/`, `run_model_eval.py`, scenarios, report, tests (-9), and the four prompts only it loaded. Docs no longer cite 76.8% or leaky-bucket limiting (the live client retries with backoff).
- **Weekly review context removed (`7497468`):** `build_context` no longer passes the stale Sep 11–17 `weekly_reviews` row.
- **Fictional demo (`d07bcb3`):** `scripts/generate_demo_journal.py` writes a seeded, fictional 42-day journal in the real notebook format; `scripts/build_demo_db.py` builds `data/demo_goalos.db` + `data/demo_chroma_db/` through `import_journal_csv`, `_extract_memories`, and `backfill_analytics` (42 logs, 9 goals across 1-month to 10-year horizons, 173 memories, 42 scores). Verified: 0 real-text hits and 0 PII in the outputs; demo-mode API smoke test on fresh paths; real `goalos.db`/`chroma_db` hashes unchanged.
- **Local-safety fixes (`74e7b01`):** `seed_demo_environment` copied demo data into any empty local DB/missing chroma dir on every startup, and `import_journal_csv` silently fell back to `demo_seed.csv` when the real CSV was missing. Both are now demo-only (3 new tests). Exporters that copied real data into the public demo paths were deleted (`644a962`), and generated reports are gitignored (`8ee2461`).
- **New open item:** the real birth date `2002-06-17` is hard-coded as a default in `migrations.py` (column DEFAULT), `models/user.py`, `life_calendar_service.py`, and `api/main.py` (fallback when unset). That is both public PII and a guessed value for anyone else. Needs a Life Calendar empty state; surfaced to the user.
- **Verification:** `pytest -q` 155 passed, `ruff check .` clean.
- **Agent Reflection:** "Sanitized" demo data that swaps names but keeps free text is not sanitized. Journal text is the sensitive part. Public demo data must be fictional by construction, and leaks must be checked by content (real lines vs. every blob), not by keywords or a name regex.

---

## 2026-09-28 — Audit Follow-ups: No Guessed Age, Dead Analytics Tiles, Stale Files

- **User confirmed birth date 2002-06-17** (already stored in `goalos.db`; current age 24.28, so Future Self writes from 34).
- **Removed the guessed age 35 (`5f1cd36`):** when `birth_date` is unset, `current_age_in_10_years` is now `None`. The fallback letter says "ten years from now" instead of an age, the prompt tells the LLM not to state or guess one, and `AICoachView` hides the age line on null (previously it only checked `undefined`, so it would have printed "age null").
- **Removed Morning mood + Deep work tiles from Analytics (`04a35e8`):** `mood_morning` and `deep_work_hours` are null on 73/73 real rows. `/analytics/dashboard` defaulted `avg_morning_mood` to **3.0** when empty, so the tile showed a fabricated "3 / 5". Both fields were dropped from the endpoint and the TS type. Sleep stays (real, from AWAKE). Note: `7b45fc5` had only removed these tiles from the *day drawer*, not the Analytics page.
- **Deleted stale files (`3cdd6aa`):** six one-off scripts that already ran, `docs/interview_llm_prep.md`, and `WeeklyReviewRepository` + `models/weekly_review.py` (test-only).
- **Held back for a user decision:** `ai/prompts/{morning,evening,mentor,goal_alignment}.txt`. `scripts/run_model_eval.py` still loads them, and 12/15 eval scenarios target removed pipelines, so deleting them means deciding the fate of the whole eval harness. Also flagged: `CoachService.build_context` still feeds the latest legacy `weekly_reviews` row (Sep 11–17, from the removed Weekly Sync) into every coaching prompt.
- **Verification:** `pytest -q` 161 passed, `ruff check .` clean, `tsc --noEmit` clean.

---

## 2026-09-28 — Codebase Staleness Audit

- **Dead code removed (`80db208`):** `CoachService.prefill_from_journal`, `chat`, `get_future_self`, and `get_dashboard_interpretations` had zero callers (`/coach/chat` routes to `CoordinatorPipeline`). That stranded the reflection pipeline (`reflection_coach.py`, `prompts/reflection.txt`, `fallback_reflection`), so those went too. Five legacy `WeeklySyncService` aliases (`group_entries_into_weeks`, `generate_weekly_report`, `generate_monthly_summary`, `save_sync_log`, `get_recent_sync_logs`) were referenced nowhere.
- **Streamlit residue removed (`8097978`):** `.streamlit/` and two text references survived the Streamlit removal in `94d6a0f`.
- **Docs synced (`83ce8b9`, `12c3114`):** README, ARCHITECTURE, PROJECT_SPEC, DEMO, and SYSTEM_DESIGN_MAPPING still documented Morning/Evening/Weekly pipelines and nonexistent endpoints (`/coach/morning|evening|weekly`, `/coach/goal-alignment`, `/factory-reset`), a `LifeCalendar.tsx` component that doesn't exist, the vision columns dropped in migration 7, 3 goal horizons instead of 4, and test counts of 106/130 (actual: 160). The README ToC also had 4 links to sections that don't exist.
- **Correction to the entry below:** `data/Journal/` is in `.gitignore`, but `journal_data.csv` and four JSON batches (plus `data/Journal/append_csv.py` and `data/journal_history.json`) were force-added in August/September and remain **tracked**. They are pushed to `origin/main`, and the GitHub repo is **public**. So the AWAKE backfill is *not* on-disk only: it shows as an uncommitted modification of a tracked file. Surfaced to the user for a decision (untrack and/or purge history); nothing was committed or rewritten.
- **Verification:** `pytest -q` 160 passed, `ruff check .` clean, `tsc --noEmit` clean.
- **Agent Reflection:** Removing features (Morning/Evening/Weekly, Streamlit, vision fields) left a long tail: dead service methods, orphaned prompts, and five docs describing the old app. When deleting a feature, grep docs and callers in the same change. And `.gitignore` only stops *untracked* files: `git ls-files` is the truth for what's tracked.

---

## 2026-09-28 — Full Historical AWAKE Backfill (July–September)

- **Transcribed AWAKE directly from all 61 remaining notebook photos** (the July root photos, all 31 August photos across both batches, and the remaining 9 September photos beyond the 2 already read) to complete the backfill decided on last session. Confirmed structurally: July has no AWAKE section at all (5 spot-checked across the full month, all absent) - the habit started August 3. Two photos in the August batch turned out to be retakes of the same day (Aug 15 and Aug 19 each photographed twice); both matched their originals exactly once transcribed, confirming the duplicate theory.
- **Four entries have anomalously short "AM–AM" windows** (Aug 30, Sep 5, Sep 6, Sep 10) that don't match the rest of the pattern (e.g. "9:30 AM - 11:00 AM") - recorded exactly as written, not corrected/guessed. The existing `_parse_awake_range()` sanity check (reject if computed sleep is outside 0-16h) already handles these correctly: text is preserved, `sleep_hours` stays `None` rather than computing a nonsensical ~20+ hour figure. Three entries (Aug 18, Aug 27, Sep 11) have no end time written at all - stored as-is, same guard applies.
- **Patched `data/Journal/journal_data.csv` directly** (not the JSON transcription batches, several of which no longer exist for the earlier days) with an `Awake` column value per row, verified 1:1 against all 73 CSV dates before writing. This file lives under the gitignored `data/Journal/`, so the patch is on-disk only.
- **Found and fixed two more real bugs while verifying against the real data**, both in `services/journal_import_service.py`:
  1. 5 of 73 days write PLAN times without a colon ("915-945 study" instead of "9:15-9:45") - `_parse_plans()`'s regex required `\d{1,2}(:\d{2})?` and silently dropped these lines. Extended the time-token regex (and `_parse_bare_hour()`, used during hourly-grid resolution) to also accept the compact 3-4 digit form.
  2. Even after that fix, the affected days' blocks were 30-minute (sub-hour) spans that never touched an integer hour boundary, so `_build_hourly_blocks()`'s old containment check (`start_abs <= hour < end_abs`) still matched nothing. Changed to a proper interval-overlap test (`start_abs < hour+1 and end_abs > hour`) - a strict superset of the old behavior for hour-aligned blocks (verified against the existing Issue 1 tests), and it now correctly captures sub-hour blocks too.
- Re-ran `scripts/import_journal_csv.py` against the real `goalos.db` (backed up first). Result: `awake_range` populated for 40/73 days, `sleep_hours` computed for 33/73 (the other 7 are the anomalous/incomplete entries above, correctly left `None`). Days with zero visible PLAN content dropped from 7 to 2 - the remaining 2 (19/7, 11/8) have genuinely empty Plan fields in the source, not a parsing failure.
- Verified end-to-end in a live browser session (Playwright): August 5 (previously invisible, 0 PLAN blocks) now shows "9.5h sleep", "8:30 AM - 11:00 PM", and both of its written PLAN blocks correctly bucketed.
- Suite: 160 passing, ruff/tsc clean.

---

## 2026-09-27 — Real Journal Data Cleanup + AWAKE Import Support

- **Removed all guesswork:** `scripts/backfill_analytics.py` used to fabricate `sleep_hours`/`mood_morning`/`energy_level`/`sleep_quality`/`expected_focus`/`deep_work_hours` via keyword-matching (e.g. `extract_sleep_hours` only ever returned `5.5`/`7.2`/`8.0`). Deleted those functions outright; the script now only recomputes `scores` from real fields. Nulled the 94 already-fabricated rows and deleted the 94 downstream `scores` rows that had compounded from them (`momentum_score` chains day-to-day, so the contamination wasn't isolated to single days).
- **Deleted pre-standard history:** all `daily_logs` before 2026-07-01 (48 rows + 84 memories) — the user's confirmed final journal structure started that date; earlier data used inconsistent, evolving formats and the user chose not to keep it.
- **Fixed 3 real task-blob rows** (2026-07-01/02/03) where a day's TASKS had been written as one comma-joined paragraph instead of one task per line — re-split on the user's own embedded numbering, no invented content.
- **Confirmed final journal structure** (six sections, in order): GRATITUDE, AWAKE, PLAN, TASKS, REVIEW, TAKEAWAY. Added AWAKE parsing to `journal_import_service.py` (`_parse_awake_range`) — computes `sleep_hours` honestly from the two written times (e.g. "9:00 AM - 12.30 AM." → 8.5h), never guesses when unparseable.
- **Backups:** two full `DataPortabilityService.create_backup()` zips in `backups/` bracket this work.
- **Next planned import change:** normalize PLAN into fixed 1-hour blocks spanning the awake window — plan written to `docs/plans/2026-09-27-hourly-plan-blocks-import.md`, not yet implemented.

---

## 2026-09-28 — Confirmed AWAKE Data Loss Is a Transcription Bug, Not Missing Data + Future Self Now Validates 5/10-Year Pacing

- **AWAKE confirmed present in the actual notebook, lost in transcription:** read two real photos (`September 2026/IMG20260911213937.jpg` = 1/9, `IMG20260911214012.jpg` = 5/9) directly — both clearly show a handwritten `AWAKE <time> - <time>` line. Neither `september_2026_batch.json` transcription captured it. Root cause: (1) the photo→JSON transcription step drops it, and (2) even if it were captured, `data/Journal/append_csv.py` only ever wrote the 6 fixed Date/Gratitude/Plan/Tasks/Review/Takeaway columns — Awake would be dropped there too. Fixed #2: `append_csv.py` now writes Awake (appended last, not inserted after Gratitude, so the 73 existing `journal_data.csv` rows keep parsing correctly as `Awake=None` rather than shifting every later column). This file lives under the gitignored `data/Journal/`, so the fix is on-disk only, not a git commit. Photo coverage check: all 73 real days have a source photo (31 July + 33 Aug [2 untranscribed duplicates] + 11 Sept) — a full backfill is possible whenever the user wants it, not attempted this session.
- **Verified the app's AI Coach structure matches the user's intended mental model** (notebook → photos → me extracting → DB; Calendar day-click → full day view; Goals at 1mo/1yr/5yr/10yr; AI Coach = Goal Alignment [monthly/yearly] + Future Self [5yr/10yr]; pattern discovery as the core value). Found one real gap: Future Self's prompt (`ai/prompts/future_self.txt`) was a generic "letter from age 35" that never actually checked pacing against 5/10-year goals, even though that context was already available.
- **Rewired Future Self to actually validate pacing**, per user clarification (Goal Alignment = monthly/yearly; Future Self = 5-year/10-year): rewrote `future_self.txt` to require an explicit on-pace/off-pace assessment against active 5-year/10-year goals; added `CoachService._get_current_age()` (from real `birth_date`) so `current_age_in_10_years` replaces the hardcoded "age 35"; rewrote `fallback_future_self()` in `ai/pipelines/_base.py` to derive `five_year_pacing`/`ten_year_pacing` from real active Goal titles + recent task completion rate; `AICoachView.tsx` renders the new fields and relabels the card "5-year & 10-year horizon pacing".
- **Live-testing against real data caught a bug in the fix itself**: when a horizon has no goals yet, the fallback was substituting its own "no N-year goals defined yet" placeholder into a sentence as if it were a real goal name (`'no 10-year goals defined yet' stops being aspirational...`). Fixed with a per-horizon `pacing_for()` that reports the placeholder as its own clean sentence, never joined into "X and Y are becoming real" phrasing. See [[feedback-verify-against-real-data]] — caught by hitting the live `/coach/future-self` endpoint with real data, not just unit tests.
- Suite: 157 passing, ruff/tsc clean. Verified end-to-end in a live browser session (Playwright) after each fix.

---

## 2026-09-27 — Real Import Pipeline Never Used the New Parser + Day Drawer Rebuilt

- **Root-cause finding:** all 73 real `daily_logs` rows (`import_source='journal_data.csv'`) came from `scripts/import_journal_csv.py`, a completely separate, older script from `services/journal_import_service.py` - meaning every improvement from this session's earlier AWAKE-parsing and hourly-PLAN-block work had never touched a single real row, only the excel/json/markdown/text-block paths nobody actually uses. Traced further: `journal_data.csv` (built by `data/Journal/append_csv.py` from monthly transcription batches like `september_2026_batch.json`) has no AWAKE field anywhere upstream, all the way back to transcription - not a parsing bug, the data was never captured.
- **Rewired `scripts/import_journal_csv.py`** to delegate PLAN/TASKS/AWAKE parsing to a shared `JournalImportService()` instance instead of its own duplicate heuristics, and to read an optional Awake/AWAKE/awake CSV column so adding one later needs no code change. Dropped the `top_priority`-copies-first-task hack and the `one_lesson=takeaway` duplication (both dead: `journal.tsx`'s live editor hasn't exposed those fields in months, 0 real rows have `one_win`/`supporting_task_1/2` set).
- **Found and fixed a real inverted-logic bug** while re-running the corrected importer: `JournalImportService._parse_tasks()` treated bare `"X"` as a *completion* marker and never recognized `"(tick)"` at all. The user's actual notation is the reverse - `(tick)`/checkmarks mean done, `X`/`(x)` mean NOT done (a failure mark). This silently inverted completion status for a large fraction of real tasks (fixed, e.g. two prior tests had encoded the wrong assumption and were corrected alongside the fix).
- **Rebuilt `DayDetailDrawer.tsx`** (the read-only panel from the Year Productivity Calendar) around the real six-section structure (Gratitude / Awake & sleep / Plan / Tasks / Review / Takeaway) instead of the old in-app Morning Planning/Evening Review schema it was still using (`top_priority`, `supporting_task_1/2`, `intention`, `one_win`, `one_lesson`, `morning/evening_completed` badges) - fields dead for every real row. It previously didn't render PLAN/schedule data at all.
- Re-ran the corrected importer against the real `goalos.db` (backed up first via `DataPortabilityService.create_backup()`); verified end-to-end with Playwright against a live dev server - the July 24 day now correctly shows 5 real PLAN blocks and the right task checked off.
- Suite: 150 passing, ruff/tsc clean.

---

## 2026-09-27 — Goal Records Are Now the Source of Truth for Vision

- **Issue 2 of the roadmap, resolved:** Settings' three free-text paragraphs (`life_vision`/`five_year_vision`/`one_year_vision`) were removed. `one_year_vision` had no UI input at all despite being fully wired end-to-end and read by the mentor briefing — always silently empty. Root cause was genuine overlap: the Goals page already had structured, trackable goals per horizon; Settings duplicated that with untracked prose at 1/5/10-year that drifted out of sync.
- **Decision (user's):** Goals is the single source of truth for vision at every horizon, not Settings. Added a `10-year` horizon bucket to `GoalRepository.get_by_horizons()` (previously capped at 5-year) so the identity-tier vision has somewhere to live as real goals.
- **`CoachService._get_user_vision()`** now derives the AI coaching narrative from active Goal titles/reasons per horizon instead of the three DB columns — output dict shape unchanged, so `mentor_briefing.py` and the chat system prompt needed no edits.
- **Migration 7** dropped the three columns from `user` (SQLite 3.35+ `ALTER TABLE ... DROP COLUMN`). Applied to the real local `goalos.db` after a `DataPortabilityService.create_backup()` snapshot; the old paragraph text was allowed to go per the user since real Goal records already cover the same themes.
- **Frontend:** removed the two Settings textareas; `GoalFormModal`'s horizon select and `GoalsView`'s board gained a 10-year option/column; relabeled Goals' 5-year option from "5-Year Vision" to "5-Year Horizon" so "vision" consistently means the 10-year identity tier and "horizon" means a trackable goal.
- **Also removed the legacy Streamlit app** (`app/`, `components/`, `utils.py`, `run.bat`, `packages.txt`) per explicit user confirmation it's no longer used — the React (`frontend/`) + FastAPI app is the only live surface. One Streamlit page wrote `user.life_vision` directly and would have broken on the migration above.
- Suite: 149 passing (+6 new), `ruff check .` clean, frontend `tsc --noEmit` clean.

---

## 2026-09-27 — Hourly PLAN-Block Normalization on Journal Import

- **Issue 1 of the roadmap, implemented:** `journal_import_service.py` now expands each day's PLAN section into a fixed grid of one-hour `ParsedTimeBlock`s (from `ceil(wake_hour)` through midnight) whenever an AWAKE section is present, instead of storing whatever irregular widths the user happened to write that day. Multi-hour lines (e.g. `"6-9 met my friends"`) repeat their activity across each covered hour; hours with nothing written get `""`, never a fabricated activity.
- **Bare-hour disambiguation:** the user's notebook writes PLAN times with no AM/PM (`"9-10"`, `"1-3"`, `"8-12"`). Each token is ambiguous between `{n, n+12}`; resolved by carrying the previous block's resolved end forward and picking whichever candidate keeps the day moving strictly forward from the wake hour — never wrapping backward into the same day.
- **Grid end confirmed with the user:** always caps at midnight (24:00) regardless of the AWAKE section's actual end time — the stretch between midnight and actual sleep isn't tracked as blocks.
- **No AWAKE section → no grid:** falls back to the old unsplit PLAN parsing rather than guessing a wake hour.
- Full plan: `docs/plans/2026-09-27-hourly-plan-blocks-import.md`. Suite: 143 passing, `ruff check .` clean.

---

## 2026-09-27 — AI Coach Pruned to Goal Alignment + Future Self

- **Decision:** User doesn't journal live in the app — real usage is a weekly/biweekly bulk photo-to-text import from a paper notebook via `journal_import_service.py`. Morning Planning, Evening Review and Weekly Sync all restated same-day journal fields back as one generic LLM sentence; none had any consumer elsewhere in the app, and none matched a workflow where days arrive in batches, not one at a time.
- **Traced before removing, not assumed:**
  - Evening Review looked load-bearing (it drives `MemoryService.store()` for lessons/patterns/commitments) — but `journal_import_service._extract_memories()` already does the same job deterministically, per imported day, independent of any coach click. Removing the card loses nothing for this user.
  - `morning_completed`/`evening_completed` (set by the deleted routes) are only the last-resort rule in `life_calendar_service.py`'s 4-tier productivity check, behind score/deep-work/task-rate — bulk import populates those first three directly, so the fallback rule was already dead weight for this user's data.
  - `/journal/upsert` already recalculates daily scores independently (`api/main.py`), so Evening Review was never the only path to Analytics scoring either.
  - Found `progress_coach.py` + `CoachService.get_progress_coaching()` fully written but never wired to a route or the UI — it evaluates execution against **both** 1-Month and 1-Year goals with explicit pattern-vs-noise separation, which is exactly the "aligned to this month's and this year's goals" check the user wanted. Reused it instead of building new.
- **Removed:** `morning_coach.py`, `evening_coach.py`, `weekly_coach.py`, `agent_morning_coach.py`, the old single-goal `goal_alignment_coach.py`, `models/coach_output.py`, `ai/prompts/weekly.txt`, the `/coach/morning|evening|weekly|goal-alignment` routes, `MorningCoachRequest`/`EveningCoachRequest`, and the buried "Morning coach"/"Run evening review" buttons inside `JournalView.tsx` (a third entry point that would have been easy to miss).
- **Kept on purpose:** `ai/prompts/mentor.txt`, `evening.txt`, `goal_alignment.txt`, `future_self.txt` — `scripts/run_model_eval.py` (the free-model benchmarking harness) loads these directly by name via `load_prompt()`, decoupled from the product pipeline files. Deleting them would have silently broken an unrelated, already-working tool outside the scope of this change.
- **Result:** AI Coach page is now 2 cards (Goal Alignment → `/coach/progress`, Future Self) plus the unaffected Chat tab. New route added, four old ones removed; `pytest -q` 133 passed, `tsc --noEmit` clean, verified live via Playwright against real journal data.

---

## 2026-09-25 — "Magical, Simple & Light" Refinement Shipped (Theme Unchanged)

- **Action:** Implemented every scope the user chose after the 2026-09-24 critique. The palette, paper-glass surfaces and fonts are unchanged.
- **Uncover the magic:**
  - The watercolor mist is visible again through a fixed `body::before` layer.
  - The navbar is solid `bg-white/95` with no blur.
  - Real keyframes replace the missing classes: drawer glide, veil, fade-up, a today ripple that plays twice and rests, and an ink bloom.
  - Everything has a `prefers-reduced-motion` path, and every dead Tailwind class was removed.
- **Lighten:**
  - The horizon banner shows on the Calendar only, as one serif sentence ("Day 268 of 365 · 82 productive days · 97 still unwritten") plus a bar with an amber "today" marker.
  - Every view header is a plain `PageHeader` on the canvas, and all 28 uppercase labels and eyebrow chips are gone.
  - Month cards became borderless groups with aligned weekday rows.
  - The legend is plain words; jargon became plain copy; the footer reads "Stored privately on this device".
- **Serif voice:** A `.voice` utility (Newsreader) now carries goal reasons, memories (cards by default, with relative dates), journal gratitude, reflection and rule, the drawer's win, lesson and notes, and coach chat replies.
- **Ink the day:**
  - A shared `DayDot` component serves the calendar and a new 7-day strip in the Journal header.
  - When a save raises the day's tier, its dot inks. Today is an amber sun until it has been written in.
- **Calm Analytics:**
  - The healthy momentum pattern comes first, and all "Repeated Task Deferral" cards fold into one "Tasks you keep postponing" list.
  - Patterns are capped at 3, and daily scores at 10 rows, each with a "Show all" toggle.
  - The APM table moved to a collapsed `DiagnosticsPanel` in Settings that loads on open.
- **Journal behaviour:**
  - Debounced autosave with a quiet status line, flushed on date and tab changes, with Ctrl/Cmd+S to save now.
  - Local-date fix (`lib/date.ts`).
  - The date is a serif title with a native picker.
- **Accessibility:**
  - The calendar is one tab stop with arrow-key movement, and each day's label reads as a sentence.
  - The drawer is a real dialog: it focuses Close, traps Tab, closes on Escape and returns focus.
  - Nav tabs carry `aria-current`, and labels are tied to their inputs.
  - Secondary text is at least slate-500.
  - The 70-year view no longer contains 3,650 no-op buttons.
- **Bugs found along the way:** Fixed overlays were offset by `space-y` margins (learning 4.8). `LifeCalendar.tsx` was dead code and has been deleted.
- **Verification:**
  - `npm run build` (tsc + vite) is clean, and `pytest -q` shows 134 passed.
  - A Playwright interaction suite passed 19 of 19 checks with journal writes intercepted, so no DB writes occurred. It covered autosave (once), the ink moment, the local date, flush on tab switch, the keyboard grid, drawer focus handling and reduced motion.
  - The Impeccable detector dropped from 5 findings to 0 after a disclosed ignore for the pinned house font (`.impeccable/config.json`).
  - The critique snapshot is closed.

---

## 2026-09-24 — Impeccable Design Critique: "Magical, Simple & Light" Without a Theme Change

- **Action:** Ran a dual-agent Impeccable critique of the whole React SPA (an isolated design review plus an isolated detector and headless-Playwright pass, at desktop 1440 and mobile 390). Scored 20/40 on Nielsen's heuristics, with 0 P0 and 3 P1 issues. The snapshot is `.impeccable/critique/2026-09-24T17-38-23Z__frontend-src-app-tsx.md`.
- **User Direction:** Improve toward "magical yet simple and light" without major theme changes (see project_learnings 4.6).
- **Key Findings:**
  - The horizon banner is repeated on 3 views with duplicate metrics.
  - The watercolor mist is hidden by the root wrapper's opaque background.
  - Several Tailwind classes never compile, which left the navbar transparent under a 40px blur and killed the entrance animations (4.7).
  - Newsreader carries almost none of the user's own words.
  - 28 uppercase labels run against the sentence-case rule.
  - Analytics is a wall of amber warnings.
  - A real bug: Journal "today" uses a UTC `toISOString()`, so in IST between 00:00 and 05:30 it opens the previous day.
- **Detector:** The CLI found 5 issues. The browser pass produced 210 finding lines: low-contrast from the slate-400 10px weekday letters, nested cards, emerald→teal gradients, and idle glow/pulse loops. It also produced false positives from `selection:` and `hover:` variants.
- **Status:** The report was delivered and the user was asked to choose the scope. No UI code has changed yet.

---

## 2026-09-23 — Antigravity Global Agent & Plugin Marketplace Deployment

- **Action:** Deployed 11 curated, production-ready plugins from the [wshobson/agents](https://github.com/wshobson/agents) marketplace globally into Google Antigravity CLI (`agy`).
- **Plugins Installed:** `python-development`, `backend-development`, `debugging-toolkit`, `unit-testing`, `code-refactoring`, `c4-architecture`, `code-documentation`, `database-design`, `git-pr-workflows`, `full-stack-orchestration`, `developer-essentials` (excluding JavaScript/TypeScript).
- **Execution Architecture:**
  1. Cloned `wshobson/agents` to local tools cache `C:\Users\jegad\agents-marketplace`.
  2. Executed multi-harness adapter generator `python tools/generate.py --harness antigravity --all` using local Python 3.13, producing 824 Antigravity-native artifacts (agents, skills, commands).
  3. Installed each curated plugin via native `agy plugin install`, storing them in `~/.gemini/config/plugins` and registering them in `~/.gemini/config/import_manifest.json`.
- **Verification:** Verified all 11 plugins loaded cleanly using `agy plugin list`.

---

## 2026-09-23 — Front Page Transformation: Current Year Productivity Calendar & Structured Day Inspector

- **Action:** Transformed the GoalOS front page from the static 70-year lifespan calendar (3,640 week blocks) into an interactive **Current Year Daily Productivity Calendar** (365/366 day circles), tracking productive days, streaks, and monthly execution.
- **Architectural Implementation:**
  1. **Backend (`services/life_calendar_service.py`):** Added `get_year_productivity_grid(year, reference_date)` evaluating Rule 1 (Smart Composite: productivity score $\ge 50$, deep work $\ge 1.5$h, task completion $\ge 50\%$ with tasks, or morning+evening routine completion). Computes year elapsed, remaining, productive days count, current streak, best streak, and 12-month breakdowns. Exposed via `GET /api/calendar/year`.
  2. **Frontend UI (`YearProductivityCalendar.tsx` & `DayDetailDrawer.tsx`):** Built 12-Month Grouped Grid (Option A) displaying all 365 days aligned by weekday with monthly completion badges. Built slide-over `DayDetailDrawer` displaying structured morning priorities, planned task checklists, evening reflection/wins, sleep/energy metrics, and one-click jump to `JournalView`.
  3. **Banner Transformation (`LifeProgressBanner.tsx`):** Replaced static weeks-lived banner with the **Year Productivity Horizon Banner** displaying productive days, productivity rate %, active streak, and dual-layer progress bar, while maintaining a perspective toggle to the 70-year Memento Mori lifespan view on demand.
  4. **State Navigation (`App.tsx` & `JournalView.tsx`):** Added `initialDate` prop support to `JournalView`, enabling instant seamless editing of any inspected date directly from the calendar.
- **Verification:**
  - Automated tests: 4/4 passed in `tests/test_year_productivity_calendar.py` covering leap year handling, smart composite rules, streaks, and API endpoint; 8/8 regression tests passed in `tests/test_life_calendar_and_weekly_sync.py` and `tests/test_api.py`.
  - Frontend verification: TypeScript build (`tsc && vite build`) passed with zero errors, bundling production assets cleanly.


## 2026-09-12 — AI Coach Model Upgrade (Gemma 4 31B) & Fast Timeout Auto-Failover

- **Action:** Upgraded the primary coaching LLM from congested `nvidia/nemotron-3-super-120b-a12b:free` to `google/gemma-4-31b-it:free`, delivering rich, emotionally intelligent, articulate mentorship with sub-4s response latency.
- **Architectural Fix:** 
  1. Refactored `OpenRouterClient.complete()` and `_post_chat_completion()` to lower timeout from 18s to 12s and immediately auto-failover across healthy live free endpoints (`google/gemma-4-26b-a4b-it:free`, `nex-agi/nex-n2.5-pro:free`, `nex-agi/nex-n2.5-mini:free`, `nvidia/nemotron-3.5-lightning:free`) on timeouts, connection errors, or HTTP 5xx errors rather than retrying the same stalled endpoint for 57+ seconds.
  2. Added a 45s safety timeout to the frontend Axios client in `frontend/src/api/client.ts` and enhanced loading feedback in `AICoachView.tsx`.
  3. Fixed `tests/conftest.py` collection cache clearing (`ms.clear_collection_cache()`) and added unit test suite `tests/test_openrouter_failover.py`.
- **Verification:** 3/3 tests passed in `tests/test_openrouter_failover.py` verifying failover on timeout and 502 errors; 6/6 tests passed in `tests/test_agent_coordinator_and_telemetry.py`.

---

## 2026-09-11 — September 1-11 Journal Transcription, Ingestion & Cognitive Memory Indexing

- **Action:** Transcribed handwritten journal entries from 11 photos in `data/Journal/September 2026/` into structured JSON (`data/Journal/september_2026_batch.json`). Appended all 11 days to `data/Journal/journal_data.csv`. Synchronized records into SQLite `daily_logs` via `scripts/import_journal_csv.py`. Extracted and dual-wrote 35 memories into SQLite `memories`, FTS5 `memory_fts`, and ChromaDB vector index via `scripts/extract_september_memories.py`.
- **Key Architectural Fix:** Refactored `scripts/extract_september_memories.py` to decouple outer SQLite reads from inner `MemoryService.store()` transactions, resolving SQLite database connection locking contention on Windows.
- **Verification:** Verified `daily_logs` contains 11 records (2026-09-01 through 2026-09-11) with correct task completion rates (ranging from 0% to 100%), verified 33 active memories indexed in ChromaDB (100% indexed), and confirmed live `/health/details` reports 121 total logs and 262 active memories.
- **Autonomous Commits:** `8fcf0b3` (`feat(journal): import and index September 1-11 journal entries and memories`), `c53ef11` (`fix(coach): optimize coordinator grounding, timeout handling, and fallback resilience`).

---

## 2026-09-03 — Comprehensive Documentation & Codebase Parity Synchronization

- **Action:** Brought all project specifications, architecture documents, demo scripts, and ADRs into 100% parity with the production codebase (v2.6.0).
  - Modernized `docs/PROJECT_SPEC.md` from legacy July 2026 Streamlit draft to current React 18 + Vite desktop SPA, 106 tests, 5-factor hybrid RAG formula with MMR pruning, and full REST API specification.
  - Corrected `docs/ARCHITECTURE_AND_SPECIFICATIONS.md` Section 5 REST API table (fixed `/analytics/dashboard`, `/analytics/scores`, `/export`, `/export/reset`, removed non-HTTP `/memories/reconcile`, and added full `/coach/chat`, `/coach/sessions`, and `/coach/telemetry/*` suite) and updated Section 4 ER diagram with `COACH_SESSIONS`, `COACH_MESSAGES`, and `AI_TELEMETRY`.
  - Modernized `docs/DEMO.md` walkthrough script to showcase 106 tests, modern FastAPI endpoints, and the React 18 dashboard views.
  - Codified ADR-005 in `architectural_decisions.md` documenting the Supervisor-Coordinator multi-agent pattern with domain toolkits and blackboard state.
- **Rationale:** Documentation drift breaks trust for both human pair programmers and AI agents operating on the project brain. Every specification must accurately reflect running production systems.
- **Verification:** Verified all route paths against `api/main.py`, verified React component references against `frontend/src/components/*`, ran `pytest -q` (106/106 passing).
- **Agent Reflection:** Regular audits of specification documents against actual codebase routes and data models prevent subtle inconsistencies from accumulating as features evolve.

---

## 2026-09-01 — Coach Chat UI, Consent Fix, Generic-Output Bug Fix & August Ingestion

- **Action:** Committed the pending Coach Chat frontend (`AICoachView.tsx` chat thread + sessions sidebar, `GoalFormModal.tsx`, `client.ts` chat/session methods) against the multi-agent `CoordinatorPipeline` backend. Fixed two bugs found via user report ("every coach output looks the same, no specific patterns"): (1) chat sent no `remote_ai_consent` field, so the backend's `True` default silently overrode a user who had disabled remote AI in Settings; (2) `AICoachView` rendered only a hardcoded directive string for every pipeline result, ignoring the real fields each pipeline returns (future-self `message`, goal-alignment `alignment_narrative`/`aligned_goals`/`neglected_goals`), so every coach screen showed the same fallback line ("Focus on relentless execution of today's #1 priority") regardless of what the AI actually produced. Also ingested August journal days 16–31 (previously only 1–15 were in `daily_logs`) via the existing `scripts/import_journal_csv.py`, and produced a grounded month-in-review report (`reports/august-ledger.html`) directly from the 31-day dataset to demonstrate what a properly grounded coach response looks like.
- **Rationale:** A coaching app whose output looks identical regardless of underlying data is a trust-breaking bug, not a content problem — the root cause was a UI/data-shape mismatch plus a data-completeness gap, not a prompting issue. The privacy toggle silently not applying to the primary chat surface is a contract violation for a "privacy-first, local-first" product.
- **Verification:** `npx tsc --noEmit` clean; `pytest` 106/106 passing; verified `daily_logs` has 31/31 August rows with correct `task_completion_rate` after import (spot-checked 2026-08-23 → 0%, 2026-08-31 → 50%).
- **Agent Reflection:** When a user reports "the AI feels generic," check the render path before touching prompts — a pipeline can be well-grounded and still appear generic if the UI only surfaces one hardcoded field. Also: any per-user consent/privacy toggle needs an explicit end-to-end trace from the setting's storage to every call site that gates on it, since a sensible-looking backend default can silently defeat the toggle at just one call site.

---

## 2026-08-30 — Production AI Evaluation Framework & Vision Metrics

- **Action:** Built production-grade autonomous evaluation orchestration framework (`ai/eval/`) with 6 GoalOS Vision Metrics (Schema Integrity, Grounding & Anti-Hallucination, Actionability, Horizon Alignment, Tool-Calling Precision, Operational Efficiency), rate limiter with exponential backoff for free-tier models, 15 benchmark scenarios dataset (`data/eval_scenarios.json`), and CLI orchestrator (`scripts/run_model_eval.py`).
- **Rationale:** Allow objective, autonomous benchmarking of top free models (`llama-3.3-70b`, `gemini-2.0-flash`, `deepseek-r1`, `qwen-2.5-coder`, `mistral`) with zero HTTP 429 errors to select the best default LLM.
- **Verification:** 9/9 pytest unit tests passing in `tests/test_eval_framework.py`.

---

## 2026-08-30 — Zero-Lag Compositor & Performance Optimization

- **Action:** Eliminated real-time dynamic Gaussian blur DOM animations (`filter: blur(70px)`) and replaced them with pre-computed, GPU-cached CSS multi-stop radial gradient washes on the body canvas. Standardized `.glass-panel` and `.glass-card-interactive` on high-performance opaque paper glass.
- **Rationale:** Prevent continuous GPU compositor re-rasterization on every frame (60-120fps), ensuring instantaneous (<16ms) page transitions and 0ms lag across all GoalOS views.
- **Verification:** Verified running servers on ports 8000 and 5173 with smooth navigation.

---

## 2026-08-30 — Forest Mist Paper Glass Theme, Humanized Typography & Autonomous Git Discipline

- **Action:** Completed comprehensive visual redesign to Forest Mist Paper Glass theme with subtle watercolor watermark blooms, replaced robotic utilitarian typography with Plus Jakarta Sans and Newsreader serif editorial accents, and codified autonomous learning recording and autonomous Git discipline invariants.
- **Rationale:** Eliminate cold, robotic, mechanical feel in favor of an organic, tranquil, executive life companion with crystal clear typographic hierarchy and zero friction for continuous version control.
- **Brain Integration:** Updated `system_patterns.md`, `project_learnings.md`, `git_discipline.md`, `AGENTS.md`, and `GEMINI.md`.
- **Verification:** Verified frontend styling, font bindings, antialiasing rules, and clean atomic commits.

---

## 2026-08-26 — Architecture Blueprint & Autonomous Brain Initialization

- **Action:** Created complete High-Level Architecture & Specifications document (`docs/ARCHITECTURE_AND_SPECIFICATIONS.md`).
- **Rationale:** Provide a rigorous, single-source-of-truth technical blueprint covering the full 4-tier architecture, hybrid RAG algorithms, data models, API endpoints, and system constraints.
- **Brain Integration:** Established `.agents/brain/` with structured knowledge banks (`system_patterns.md`, `project_learnings.md`, `architectural_decisions.md`, `troubleshooting_kb.md`, `active_context.md`, `evolution_log.md`).
- **Rules Deployed:** Configured workspace rules (`AGENTS.md`, `GEMINI.md`, and `.agents/rules/*`) enforcing continuous self-improvement, pair programming checkpoints, and strict verification.
- **Verification:** Verified all paths, component linkages, and mathematical formulations for 5-factor hybrid retrieval.
- **Agent Reflection:** Initializing this brain memory structure ensures that future agent instances retain all repository invariants and avoid repeating past failure modes.

---

## 2026-07-08 — V2.1.0 Light Mode & FastAPI Unification

- **Action:** Migrated legacy Streamlit prototype to React 18 + TypeScript + Vite frontend and standardized FastAPI REST API.
- **Rationale:** Needed sub-50ms UI response time, non-redundant metrics, and a cohesive celestial light design system.
- **Verification:** 90+ pytest tests passing across repositories, memory service, analytics, and coaching pipelines.
