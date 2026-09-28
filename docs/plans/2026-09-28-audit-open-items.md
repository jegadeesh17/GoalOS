# Audit Open Items (2026-09-28)

Open decisions left over from the 2026-09-28 codebase audit, plus how they affect the GoalOS entry on the resume. What's already done is at the bottom.

> **Status 2026-09-28 (later):** Items 1–3 are resolved; see the evolution log entry "Private Journal Purged From Public History". Item 1: all private files purged from history and force-pushed, and the Cloud Run demo now ships a fictional dataset. Item 2: eval harness deleted (`59215d1`). Item 3: weekly review removed from coaching context (`7497468`). Item 4: user decided **no resume changes**; keep working on `dev` and merge when finalized. **New open item:** the real birth date `2002-06-17` is hard-coded as a default/fallback in `database/migrations.py`, `models/user.py`, `services/life_calendar_service.py`, and `api/main.py`. It's public PII and a guessed value; replacing it needs a Life Calendar empty state.

State when written: branch `dev`, 161 tests passing, `ruff` and `tsc` clean. `dev` is 37 commits ahead of `origin/dev` (counting this file) and **not pushed** (hold until item 1 is decided). `main` is what Cloud Run deploys and what people see on GitHub.

---

## 1. 🔴 Private journal data is in the public GitHub repo (decide first)

`jegadeesh17/GoalOS` is **public**. `.gitignore` lists `data/Journal/` and `data/journal_history.json`, but these were force-added in Aug/Sep 2026 and are tracked and present on `origin/main`:

- `data/Journal/journal_data.csv`
- `data/Journal/august_2026_batch.json`, `august_2026_days16_31.json`, `batch.json`, `september_2026_batch.json`
- `data/Journal/append_csv.py`
- `data/journal_history.json`

`.gitignore` does nothing for files git already tracks. The resume links this repo, so recruiters can open these files.

`data/Journal/journal_data.csv` also has an **uncommitted** change: the AWAKE-column backfill from 2026-09-28. Leave it uncommitted until you decide.

**Options** (can combine):

| Option | Effect | Cost |
|---|---|---|
| A. Make the repo private | Stops public access immediately | Resume `[GitHub]` link breaks for recruiters |
| B. `git rm --cached` the files + commit | Stops tracking from now on; files stay on disk | Old commits on GitHub still contain them |
| C. B + purge history (`git filter-repo`) + force-push | Removes them from GitHub history | Destructive: rewrites every commit hash on `main`/`dev` |

A likely combination: **A now** (instant), then **B + C**, then make the repo public again so the resume link works.

---

## 2. Eval harness: keep, trim, or delete?

These prompts were held back from deletion: `ai/prompts/morning.txt`, `evening.txt`, `mentor.txt`, `goal_alignment.txt`. Only `scripts/run_model_eval.py` loads them, so deleting them alone would break the script. 12 of its 15 scenarios (`data/eval_scenarios.json`) target the removed Morning/Evening/Goal-Alignment pipelines. The 3 Future Self scenarios request old output keys (`future_projection`, ...) that the current prompt no longer returns.

What depends on it: `scripts/run_model_eval.py`, `data/eval_scenarios.json`, `reports/model_eval_report.md`, `ai/eval/*`, `tests/test_eval_framework.py`, plus the "76.8% composite (nemotron)" claims in `docs/PROJECT_SPEC.md` and `.agents/brain/project_learnings.md` §3.3.

**Options:**
1. **Delete** the eval harness and remove the 76.8% claims from the docs. The resume doesn't cite the 76.8% figure, so the resume is unaffected.
2. **Trim** to Future Self only, fix its expected keys, then re-run and re-report.
3. **Keep** it as a historical benchmark and label it that way in the docs.

---

## 3. Legacy weekly review still fed into every coaching prompt

`CoachService.build_context` (`services/coach_service.py`) runs `SELECT * FROM weekly_reviews ORDER BY week_start DESC LIMIT 1` and passes the result as `recent_weekly_review`. Nothing writes to that table anymore (Weekly Sync was removed). The real DB holds 4 old rows, so **Goal Alignment and Future Self both receive the Sep 11–17 review** as context.

**Options:** remove the query and context key (the table and its rows can stay for export/backup), or keep it on purpose.

---

## 4. Resume (GoalOS entry) vs. the actual code

Checked against the code on 2026-09-28:

| Resume claim | Status |
|---|---|
| 6 schema-validated tools across 4 domain namespaces | ✅ Correct (`search_memories`, `get_active_goals`, `get_horizon_pacing`, `get_recent_logs`, `get_monthly_progress`, `get_lifespan_stats`) |
| 100% (7/7) execution-reliability + unauthorized-tool-rejection benchmark | ✅ Still valid; toolkits unchanged |
| 5-factor retrieval: FTS5 lexical + Chroma cosine + recency decay + importance | ✅ Correct (0.35 sem / 0.15 lex / 0.25 imp / 0.15 recency, 30-day half-life / 0.10 frequency) |
| Failover to deterministic local heuristics offline / on rate limits | ✅ Correct (`fallback_progress`, `fallback_future_self`, coordinator rule fallback) |
| "validated by **130** automated pytest tests" | ⚠️ `dev` has **161**. Public `main` README still says 130, so the resume and `main` currently agree. |
| "personal productivity and **daily** coaching app" | ⚠️ Coaching is now batch-cadence: Goal Alignment (monthly/yearly) + Future Self (5/10-year). There are no daily pipelines anymore. |
| Summary: "281+ automated pytest tests across 4 projects" | ⚠️ 88 + 130 + 27 + 36 = 281. With GoalOS at 161 the total is **312**. |

**To keep the resume and the public repo consistent:**
1. Settle item 1 before `[GitHub]` sends anyone to the repo.
2. Merge `dev` → `main` (this triggers a Cloud Run deploy; check the live demo still works) so the public README shows 161 tests and the current feature set.
3. Then update the resume: 130 → 161, 281+ → 312+, and reword "daily coaching" (e.g. "journal-driven coaching with monthly/yearly goal-pacing and 5/10-year trajectory checks").

Do step 2 before step 3, or a recruiter will see numbers that don't match.

---

## Already done in the audit (for reference)

| Commit | Change |
|---|---|
| `80db208` | Removed unreachable CoachService methods, the reflection pipeline, and legacy WeeklySyncService aliases |
| `8097978` | Removed `.streamlit/` and leftover Streamlit references |
| `83ce8b9`, `12c3114` | Synced README / ARCHITECTURE / PROJECT_SPEC / DEMO / SYSTEM_DESIGN_MAPPING with the real app |
| `5f1cd36` | Future Self no longer guesses age 35 when birth date is unset (confirmed birth date 2002-06-17 → writes from 34) |
| `04a35e8` | Removed Analytics Morning mood (showed a fabricated 3.0/5) and Deep work tiles; both are empty in real data |
| `3cdd6aa` | Deleted 6 one-off scripts, `docs/interview_llm_prep.md`, `WeeklyReviewRepository` |
| `947e4a7`, `44be3ac`, `96dc903` | Brain / test-count updates |
