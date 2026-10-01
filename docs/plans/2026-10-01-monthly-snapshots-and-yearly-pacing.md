# Monthly Analytics Snapshots, High-ROI Levers & Yearly Goal Pacing (2026-10-01)

> **Status: M1–M4 built on `dev` on 2026-10-01.** As-built differences from the text below:
> - `monthly_goal_results` has an `as_of DATE` column (when the state was recorded) and no `tasks_done_linked`; that column waits for the task-link work in the alignment plan. It has no foreign key to `goals`, so history survives a goal being renewed or deleted.
> - Goal results are written only while the month is current or previous **and** not yet final; once a month is final they are frozen. Old months never get invented goal state.
> - `parent_goal_id` was not built (flat goals).
> - Lever tiers use a Bonferroni correction across the levers actually tested: **strong** = `p x tests < 0.05`, **suggestive** = raw `p < 0.05`. Findings store `p`, `p_adjusted` and `tests`. 1,000 permutations.
> - `recompute_month(..., with_insights=False)` is used on every journal save (facts only; stored insights are kept). Import/backfill and `POST /analytics/monthly/recompute` rebuild insights.
> - Without a `start_value`, the first check-in is the baseline, and pace is only reported from the second check-in.
> - Migration number is 8 (the alignment plan's migration becomes 9).

Goal behind this plan: every month gets a stored, comparable analytics record, and the coaching agent uses those saved months, not a single 30-day window, to judge how far the user is from their yearly (and later 10-year) goals, while surfacing the few levers that measurably move their days. Self-contained: a cold agent can implement it. Evidence below comes from the real `goalos.db` (92 days, 2026-07-01 → 2026-09-30) on branch `dev`, read-only.

Builds on `2026-10-01-goal-alignment-and-consistency.md` (task→goal links, new alignment/consistency scores). Milestone M1–M2 do **not** depend on it; goal-linked effort in M3 gets richer once it exists (until then those fields are `null`, never zero).

## 1. What the real data says (why these metrics)

Spearman correlation with same-day task completion rate, permutation test (2,000 shuffles). With ~8 variables tested, treat p < 0.01 as strong and p < 0.05 as suggestive only.

| Lever | ρ | n | p | Plain reading |
|---|---|---|---|---|
| Wake time (later = bigger) | −0.37 | 57 | 0.005 | Wake ≤ 7:30 → 62% of tasks done (n=18). Wake ≥ 8:30 → 37% (n=31). **Strongest lever.** |
| Plan hours filled in the PLAN grid | +0.28 | 92 | 0.008 | Days where more hourly blocks have an activity finish more tasks. |
| Sleep hours before the day | −0.31 | 50 | 0.023 | Likely confounded with wake time (a longer sleep means a later wake). Do not read as "sleep less". |
| Last night's bedtime | −0.07 | 52 | 0.62 | No signal. |
| Yesterday's completion | +0.10 | 91 | 0.35 | No day-to-day momentum. |
| Tasks planned | −0.06 | 92 | 0.56 | Rate is flat across plan sizes. |
| Weekend, review length | ~0 | 92 | >0.3 | No signal. |

More facts that drive concrete advice:

- **Plan size vs tasks actually done:** ≤2 planned → 0.71 done/day; 3 → 1.32; 4 → 1.71; 5+ → 2.33 (rate only slips 44% → 38%). Planning more gets more done.
- **Task position:** 1st task done 53%, 2nd 44%, 3rd 47%, 4th 29%, 5th+ 24%. What is written first gets done.
- **Stuck tasks:** `Apply for 10 companies` done 1 of 4 times in September; `Apply for companies` 2 of 3. Repeated and low-completion = needs breaking down.

These are associations on small samples. The UI and agent must say so every time; never causal language.

## 2. Principles

- Every number is derived from logged data and recomputable; nothing is entered by guess. Unknown stays `null` (shown `–`), and means exclude nulls.
- Local and deterministic: no LLM computes or stores metrics. The agent only *reads* them.
- **Honest about incomplete months.** The user bulk-imports weekly or biweekly, so a month may be incomplete when first computed. Each snapshot records `data_through`; `status = 'final'` only if the month has ended **and** `data_through` is its last day, else `'provisional'`. Snapshots are cheap and idempotent, so they are recomputed after every import or journal save.
- Goal facts that change over time (title, progress, status) are **frozen per month** in their own table; everything else is derived.

## 3. Data model (migration 9, or the next free number after the alignment plan's)

Back up the real DB first (`DataPortabilityService.create_backup()`). Schema is a consequential decision: confirm with the user before merging.

```sql
CREATE TABLE IF NOT EXISTS monthly_snapshots (
  month          TEXT PRIMARY KEY,                    -- 'YYYY-MM'
  status         TEXT NOT NULL CHECK (status IN ('provisional', 'final')),
  data_through   DATE,                                -- last logged date included
  metrics_json   TEXT NOT NULL,                       -- facts, see 4.1
  insights_json  TEXT,                                -- levers, see 4.2
  schema_version INTEGER NOT NULL,
  computed_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS monthly_goal_results (    -- frozen at the time of each recompute for that month
  month             TEXT NOT NULL,
  goal_id           INTEGER NOT NULL,
  goal_title        TEXT NOT NULL,                    -- copied: titles get edited, months must not change
  horizon           TEXT NOT NULL,
  progress_at_close REAL,                             -- goals.progress, 0-1, may be NULL
  status_at_close   TEXT,
  tasks_done_linked INTEGER,                          -- NULL until task links exist
  PRIMARY KEY (month, goal_id)
);

-- Measurable targets for goals the user wants measured (all nullable; unmeasured goals stay qualitative)
ALTER TABLE goals ADD COLUMN metric_name  TEXT;       -- e.g. 'Applications sent per month'
ALTER TABLE goals ADD COLUMN metric_unit  TEXT;       -- e.g. 'applications', 'kg', 'INR'
ALTER TABLE goals ADD COLUMN start_value  REAL;
ALTER TABLE goals ADD COLUMN target_value REAL;
ALTER TABLE goals ADD COLUMN parent_goal_id INTEGER REFERENCES goals(id) ON DELETE SET NULL;  -- ⚠ optional, see 9

CREATE TABLE IF NOT EXISTS goal_measurements (        -- user-entered monthly check-ins, never derived
  goal_id INTEGER NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
  month   TEXT NOT NULL,
  value   REAL NOT NULL,
  note    TEXT,
  PRIMARY KEY (goal_id, month)
);
```

Use the existing `_add_column` helper; register in `MIGRATIONS`; extend `models/goal.py` and `goal_repository.py` for the new goal fields; new `models/monthly.py` for the snapshot and measurement models (Pydantic v2).

## 4. Computation (`services/monthly_analytics_service.py`, new)

`recompute_month(month: str) -> MonthlySnapshot` is idempotent and upserts both tables. `recompute_all()` loops months that have any log. Reuse existing pure helpers (`JournalImportService._awake_times`, the task parsing already on `DailyLog.planned_tasks`).

### 4.1 Facts (`metrics_json`)

All means skip `null`s and report the count they used (`n`).

- `days_in_month`, `days_logged`
- Tasks: `planned`, `done`, `completion_rate`, `per_day`, `solid_days` (≥50% ticked), `zero_days`, plus `weekly` = list of `{week_start, planned, done, rate}`
- Sleep: `nights_known`, `avg_hours`, `under_6`, `at_least_7`; wake and bedtime `avg` and `sd`. **Bedtimes where the awake window is under 10 h are excluded** (they are almost certainly an AM/PM slip) and counted in `excluded_bedtimes`.
- Plan: `avg_hours_filled` (blocks with a non-empty activity, per day)
- Score means: `overall`, `health`, `productivity`, `momentum`, `goal_alignment`, `consistency` (null-aware; alignment/consistency stay `null` until the redesign exists)
- `stuck_tasks`: task keys planned ≥ 3 times in the month with completion < 50% (use `task_key()` normalisation: casefold, non-word → space, collapse)
- `data_quality`: counts of days with unknown sleep and the reason (`no_prev_day`, `unparseable`, `implausible_bedtime`)
- `delta_vs_previous`: for each headline number, `this − previous month` when both are known

### 4.2 Levers (`insights_json`)

Compute over the **trailing 90 days ending at the month's last logged day** (one month alone is too small). For each candidate lever vs same-day completion rate: Spearman ρ, `n`, permutation p-value (stdlib `random.Random(seed)`, seed derived from the month string so results are deterministic and testable), and a plain-language contrast.

Candidates: wake hour, sleep before the day, prior-night bedtime (plausible only), plan hours filled, tasks planned (and tasks *done* by plan-size bucket), task position, yesterday's completion, weekend.

Output per lever: `{lever, rho, n, p, tier, direction, contrast, caveat}`.

- Skip a lever when `n < 30` or fewer than 5 values in either contrast group.
- `tier = "strong"` if p < 0.01, `"suggestive"` if p < 0.05, else not stored as a finding.
- `contrast` examples (computed, not templated guesses): "Wake ≤ 7:30: 62% done (n=18) vs wake ≥ 8:30: 37% (n=31)".
- `caveat` is always `"Association on a small sample, not proof of cause."`; for sleep also note the wake-time confound when both are present.
- Add `focus`: up to two "try this next month" lines taken from the top findings and the top stuck task, written from fixed templates filled with the computed numbers. No LLM.
- Store `method_version` in the JSON so a formula change can invalidate old insights.

### 4.3 Goals

- `monthly_goal_results`: copy every goal that existed (non-archived) that month: title, horizon, progress, status, linked-task count (if links exist, else `NULL`).
- **Pacing for goals with a target** (`YearlyPacingService.evaluate(goal_id)`): from `start_value`, `target_value`, `deadline`, the goal's `created_at` (or an explicit start), and `goal_measurements`:
  - `expected_now = start + (target − start) × elapsed_fraction` (linear)
  - `gap = latest_measurement − expected_now`, `pct_of_target = (latest − start) / (target − start)`
  - `status`: `ahead` / `on_pace` / `behind` with a ±10% band of the start→target span
  - `projection` at the deadline by linear trend **only with ≥ 3 measurements**, else `"not enough check-ins"`
  - No measurements → `"no check-ins yet"`; no target → `"qualitative goal: effort only"`. Never fabricate a number.
- **Effort-only view** for qualitative goals: monthly `tasks_done_linked` series and a "quiet" flag (no linked task done in the last 14 days).

## 5. Agent integration

- `CoachService.build_context` adds `monthly_history` (last 6 snapshots: facts and top levers only, trimmed to keep prompts small) and `goal_pacing` (output of 4.3 for active 1-year, 5-year and 10-year goals).
- New tools in `ai/tools/`, registered via `registry.py` and scoped by domain like the existing six: `get_monthly_snapshots(months: int ≤ 12)` (journal domain) and `get_goal_pacing(horizon: str)` (goals domain). Update `scripts/benchmark_tool_calling.py`, `README.md` (it says 6 tools / 7 scenarios) and `tests/test_tool_calling.py`.
- The deterministic fallback (no consent / no API key) must also use this data: `ai/pipelines/_base.py` fallbacks quote the real pacing and top lever with their `n`, and include `source = 'deterministic_rules'` as before.
- Update the prompts in `ai/prompts/` and the `progress_coach`/`future_self_coach` system prompts: cite months by name, state `n` and tier for any lever, never claim causation, and say "no measurement" rather than infer progress for unmeasured goals.
- Replace the current single-month framing in `progress_coach.py` ("current month… 1-Month and 1-Year goals") with: this month's snapshot, the trend over saved months, then yearly pacing.

## 6. API (all behind `require_api_token`)

- `GET /analytics/monthly` → list of snapshots (months ascending), `GET /analytics/monthly/{YYYY-MM}`
- `POST /analytics/monthly/recompute?month=YYYY-MM` (no month = all)
- `GET /goals/pacing` → pacing per goal; `PUT /goals/{id}/measurements` body `{month, value, note?}`; `DELETE /goals/{id}/measurements/{month}`
- Recompute triggers: end of `scripts/import_journal_csv.run_import` (every affected month), `journal_upsert` (that date's month), goal create/update/measurement change (frozen goal rows and pacing).

## 7. UI (Forest Mist Paper Glass, sentence-case, no nested cards, Tailwind 3-valid utilities only)

- **Analytics page**: a month picker (default = latest month with data). Sections: a headline table with the change from last month (use `–` for unknown); a small weekly bar series; **"What moves your days"** (levers with tier, `n`, the contrast sentence, and the caveat in smaller text); **"Try next month"** (the `focus` lines); stuck tasks; data-quality note when sleep is unknown ("3 nights unknown: bedtime looks like AM").
- A **Provisional** badge on any month where `status = 'provisional'`, with "data through 28 Sep".
- **Goals page**: pacing line under each yearly goal ("Behind: 12 of 60 applications; on pace would be 31") and a month-end check-in form (one number per measured goal, blank allowed).
- Reuse `PageHeader`, `DayDot` vocabulary, `lib/date.ts`; all HTTP through `frontend/src/api/client.ts`.

## 8. Milestones, each shippable and TDD (write each test failing first; use `temp_db`; 2-space indent in `api/`, `services/`, `database/`, `tests/`)

- **M1 – Facts snapshots**: migration (tables only), `MonthlyAnalyticsService` 4.1, recompute triggers, `GET /analytics/monthly*`. Tests: a seeded month reproduces hand-computed counts (including the sleep-unknown reasons and excluded bedtimes); provisional vs final; recompute is idempotent; delta vs previous month; null-aware means.
- **M2 – Levers**: 4.2. Tests: a constructed dataset with a planted wake-time effect yields tier `strong` with the right `n` and contrast; `n < 30` yields no finding; deterministic p-value for a fixed month seed; the sleep caveat appears when wake time is also a finding.
- **M3 – Goals & pacing & agent**: migration additions, `YearlyPacingService`, measurements API, `goal_pacing` in coach context, the two new tools, prompt and fallback updates. Tests: pacing worked example below; no measurements → "no check-ins yet"; < 3 points → no projection; tool registry rejects unknown tool still; fallback text quotes real numbers.
- **M4 – UI** (§7), then `npm run build` and a browser check against real data.

Pacing worked example: goal `1-year`, metric "Applications sent (cumulative)", start 0, target 120, created 2026-08-01, deadline 2026-12-31 (152 days), check-in on 2026-09-30 (60 days elapsed) = 25. `elapsed_fraction = 60/152 = 0.395`, `expected_now = 47.4`, `gap = −22.4` (−18.7% of the span, beyond the ±10% band) → **behind**; `pct_of_target = 20.8%`; one check-in → no projection.

## 9. ⚠ Assumptions and decisions to re-confirm with the user

1. **Yearly distance needs numbers the user must supply.** The current goals ("Getting a job", "Getting paid", "Getting Fit", "Staying Focused") have no `success_criteria`, no target, and no milestones, so the app cannot honestly say "how far" until the user defines a measurable target for each goal they want measured (and logs a monthly check-in). Qualitative goals ("Partner") stay effort-only.
2. **No 10-year goal exists yet** (the DB has 2 one-month, 3 one-year, 3 five-year goals). Pacing and the agent can only cascade to the 10-year level once one is added.
3. `parent_goal_id` (monthly → yearly → 5-year hierarchy) is optional; skip it in M3 if the user prefers flat goals.
4. Lever window = trailing 90 days; strong p < 0.01, suggestive p < 0.05; minimum n = 30; ±10% pacing band; linear pacing. Confirm or adjust.
5. Linear pacing assumes steady progress; seasonality or front-loaded goals will read "behind" early. Acceptable for v1, flag in the UI copy.
6. A "solid day" = ≥ 50% of tasks ticked (same rule as the consistency plan).
7. Data fix the user must decide: 09-05, 09-06 and 09-10 have bedtimes written as `11:00 AM` / `11:30 AM`, which knocks out sleep for 09-06, 09-07 and 09-11. If those were PM, the source (`data/Journal/journal_data.csv`, then re-run `scripts/import_journal_csv.py`) should be corrected by the user; nobody should assume it.

## 10. Verification on real data (after M1/M2)

Back up, run `recompute_all()`, then compare read-only SQL against these known facts: September = 30 days logged, 100 tasks planned, 48 done (48.0%), 18 solid days, 4 zero days, 27 sleep nights known (avg 6.93 h), wake average 07:39; August = 31 days, 126 planned, 54 done (42.9%). Spot-check the wake-time lever reproduces ρ ≈ −0.37 (n = 57) over the window ending 2026-09-30, and the plan-hours lever ρ ≈ +0.28 (n = 92).

## 11. Non-goals

LLM-computed metrics, causal claims, automatic goal-progress inference from journal text, editing historical snapshots by hand, changing how the journal is imported, and "commitment/experiment" tracking (a natural M5: record the lever the user chose for next month and report adherence and effect the month after).
