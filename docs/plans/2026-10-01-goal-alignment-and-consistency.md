# Goal Alignment & Consistency Scores: Redesign Plan (2026-10-01)

> **Status: built on `dev` on 2026-10-01.** As-built differences from the text below:
> - The migration is **version 9** (version 8 went to the monthly snapshots).
> - `task_key` already lived in `services/journal_helpers.py` and is reused; the cue normaliser in `models/goal.py` repeats its rule because models cannot import services.
> - `goal_alignment_score(logs, resolve)` returns an `Alignment(score, reviewed, completed)` tuple (coverage is a property). `recompute_all_scores(since=None)` lives in `analytics_service`; saving a journal day re-scores from that day on, because later days' 14-day windows and momentum include it.
> - Per-goal attention is measured from the **last logged day**, not today, because the journal is imported in batches; the coach prompt and fallback treat all-zero counts as "not linked yet", never neglect.
> - `services/weekly_sync_service.py` also called the old function (the monthly report's `semantic_goal_alignment`); it now uses the link-based share, is `None` when too few tasks are reviewed, and the report's composite renormalises over the known parts (the old fallback guessed 50).
> - Not built: per-goal task counts inside `monthly_goal_results` (a natural follow-up), and the section 10 items.
> - Real data after rollout: 92 days re-scored, consistency 0-71 (mean 43, hand-checked for 2026-09-30: 7 of 14 solid days, wake sd 0.93 h, 51.1), alignment unknown everywhere until tasks are linked, 133 distinct completed tasks in the review queue.

Replaces the two daily scores that stayed broken after the 2026-10-01 sleep/health/productivity fix. Written to be implemented by an agent with no conversation context. Everything below was checked against the real `goalos.db` (92 days, 2026-07-01 → 2026-09-30) and the code on branch `dev`.

## 1. Why the current scores are useless

**Goal alignment** (`goal_alignment_score` in `services/analytics_service.py`) is Jaccard keyword overlap between one day's text and the combined text of all 8 goals. Real result: 1.6–8.7%, average 4.6%, at 30% of the overall score. It cannot work with this data:

- Goals are terse (one to four words, for example `Getting a job`) and have no description or milestones.
- Tasks are free text with no goal link (`planned_tasks` JSON holds only `text` and `completed`): `Apply to ten companies`, `Reach out to a recruiter`, `Finish the assignment`, `Wash clothes.`. No word in those appears in "Getting a job".

**Consistency** (`consistency_score`) is 100 on recent days. It counts a day when `morning_completed or evening_completed`, and the importer sets both to 1 for every imported day (`scripts/import_journal_csv.py`). Also `logged days / 30` is always 100% (92 of 92 calendar days are logged), so "streak of logged days" saturates. It measures "a row exists".

Signals that do vary in the real data (trailing 14 days, sampled): days with ≥50% of tasks ticked ranged 6–11 of 14; the standard deviation of wake time ranged 0.66–1.34 h.

## 2. Principles

- **Never guess** (hard project rule): a task with no known goal is *unknown*, never "misaligned". Unknown is excluded from the score and shown as coverage.
- **Deterministic and local**: no LLM in scoring or linking. Journal text must not leave the machine.
- **Batch cadence**: the user bulk-imports weekly or biweekly. Linking is a short review pass after an import, not a daily chore. Scores use a 14-day trailing window because a single day has about 4 tasks.
- Goal records stay the single source of truth for what the user is working toward.

## 3. Goal alignment: link tasks to goals, then measure

### 3.1 How a task gets a goal (resolution order)

`key(text)` = casefold, replace every non-word character with a space, collapse whitespace. (`"Wash clothes."` and `"wash clothes"` share a key.) Resolve a task's key in this order, first hit wins:

1. **Explicit link** in `task_links` (kind `goal` with a goal, or kind `none` meaning "reviewed, serves no goal"). Overrides everything, including cues.
2. **Unique cue match**: each goal has user-authored `cues` (a list of words or phrases, each ≥ 3 characters, stored normalised). A cue matches when it is a prefix of any token of the key (so cue `appl` matches `apply`, `applications`) or, for a multi-word cue, appears as a whole-word phrase. If exactly one active goal matches, the task resolves to it. Two or more goals match: *ambiguous*, falls through to 3.
3. **Unreviewed**: no link, or ambiguous. Shown in the review queue.

No cues are pre-filled; the user writes them (the app may *suggest* cues later, never apply them). Do not match cues against goal titles.

Size of the job (measured): 390 task entries, 303 distinct keys, 267 appear once, only 133 distinct keys were ever completed. The review queue only needs completed tasks (alignment only counts those), so the backlog is about 133 keys, and a rough, illustrative cue set (apply, interview, leetcode, run, gym…) would auto-resolve roughly 40% of them. After that, new work is about 12 completed tasks per week (157 completed over 13 weeks).

### 3.2 The score

For a date D, take logs in the 14 calendar days ending on D. Over their **completed** tasks, drop *unreviewed* ones, then:

```
goal_alignment(D) = completed tasks resolved to a goal / completed tasks that are reviewed   × 100
```

- Tasks resolved to `none` count in the denominator (they were reviewed and serve no goal, for example `Wash clothes`). This is intentional: a day of chores *should* read as low alignment.
- If fewer than **5** reviewed completed tasks are in the window, the score is `None` (excluded from `overall`, shown as `–`).
- Also return `coverage = reviewed completed / all completed` so the UI can say "based on 20 of 24 completed tasks".
- Pooling counts across the window (not averaging daily ratios) keeps it stable with few tasks per day.

Worked example: window has 24 completed tasks. 14 resolve to a goal, 6 to `none`, 4 are unreviewed. Score = 14 / 20 × 100 = **70.0**, coverage = 20 / 24 = 83%.

### 3.3 Per-goal attention (new, high value)

For each active goal return `done_14d`, `done_30d`, `last_done_date`, `days_quiet` (days since `last_done_date`, or `None` if never). A goal with `done_14d == 0` is "quiet". Shown on the Goals page and passed into the coach context (`CoachService.build_context`) so Goal Alignment coaching names the neglected goals from real counts instead of keyword guesses.

## 4. Consistency: execution rhythm + wake-time regularity

For date D over the 14 calendar days ending on D, using only logged days (`L` = number of logged days):

- If `L < 7`: score is `None`.
- **Rhythm** = (days where ≥ 50% of that day's tasks are ticked) / `L` × 100. Days with no tasks do not count as solid.
- **Regularity** = `max(0, 1 − sd / 2) × 100` where `sd` is the population standard deviation (hours) of the wake times parsed from `awake_range` (first time in the string, via `JournalImportService._awake_times`). 0 h sd → 100, 2 h or more → 0. If fewer than **5** wake times exist, regularity is unknown.
- `consistency = 0.7 × rhythm + 0.3 × regularity`; if regularity is unknown, `consistency = rhythm`.

Worked example: `L = 14`, 8 solid days → rhythm 57.14; wake sd 1.0 h → regularity 50.0; consistency = 0.7 × 57.14 + 0.3 × 50.0 = **55.0**. Real data (e.g. window ending 2026-09-27: 6 of 14 solid, sd 0.87 h) lands in the 40s to 60s, so it discriminates.

Do **not** use `morning_completed`, `evening_completed`, or "logged" as inputs.

## 5. Data model (one migration, version 8 in `database/migrations.py`)

Schema change: surface to the user before merging (project rule), and back up the real DB first (`DataPortabilityService.create_backup()`).

```sql
ALTER TABLE goals ADD COLUMN cues TEXT;          -- JSON list of normalised cue strings, NULL = none
CREATE TABLE IF NOT EXISTS task_links (
  task_key   TEXT PRIMARY KEY,                    -- key(text) from 3.1
  kind       TEXT NOT NULL CHECK (kind IN ('goal', 'none')),
  goal_id    INTEGER REFERENCES goals(id) ON DELETE CASCADE,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CHECK ((kind = 'goal') = (goal_id IS NOT NULL))
);
```

Deleting a goal cascades its links away, which returns those tasks to the review queue (correct: they are unknown again). Use the `_add_column` helper the other migrations use. Register in `MIGRATIONS`. Add `cues: Optional[list[str]]` to `GoalBase`/`GoalUpdate` in `models/goal.py` and (de)serialise JSON in `goal_repository.py`.

## 6. Code changes (layering: API → service → repository)

- `database/repositories/task_link_repository.py`: `get_all() -> dict[str, TaskLink]`, `upsert(key, kind, goal_id)`, `delete(key)`.
- `services/task_link_service.py` (new): `task_key(text)`, `resolve(key, links, goals) -> Resolution(goal_id | NONE | UNREVIEWED)`, `review_queue(limit)` (distinct keys with ≥1 completion and unreviewed, ordered by completions then entries, each with an example original text, counts, last date), `goal_attention(days=14)`.
- `services/analytics_service.py`:
  - Replace `goal_alignment_score` and `consistency_score` with the pure functions in §3.2 and §4. They take the window's logs plus, for alignment, a `resolve(text)` callable. Remove the dead `embedding_fn` parameter and `_text_similarity`/`_tokenize` if nothing else uses them (check with `git grep`).
  - `calculate_daily_scores` builds the window and passes it in. Both scores may be `None`; `overall_growth_score` already renormalises over known parts.
  - Move the loop in `scripts/backfill_analytics.py` into `analytics_service.recompute_all_scores()` and make the script call it, so the API can reuse it.
- `api/main.py` (new routes, all behind `require_api_token`):
  - `GET /tasks/review?limit=50` → `{ "unreviewed_completed_keys": N, "items": [...] }`
  - `PUT /tasks/links` body `{ "key", "kind", "goal_id" }` and `DELETE /tasks/links/{key}`. Each recomputes scores via `recompute_all_scores()` (about 92 rows, cheap).
  - `GET /goals/attention?days=14`
  - Existing `PUT /goals/{id}` accepts `cues`; a cue change also recomputes scores.
- `services/coach_service.py` `build_context`: add the `goal_attention` result under a new key.
- `frontend/src/api/client.ts`: types and calls for the above.
- `frontend/src/components/GoalsView.tsx`: a "Tasks to link" section (count in the heading, sentence case, no nested cards). Each row shows the task in the serif voice, `×3 · last 28 Sep`, one chip per active goal, and a "No goal" chip. A click saves and the row leaves. Under each goal show "Moved 6 times in 14 days" or "Quiet for 21 days". Keep the Forest Mist Paper Glass tokens from `.agents/brain/system_patterns.md`; use only Tailwind 3 valid utilities.
- `frontend/src/components/GoalFormModal.tsx`: a "Task cues" field (comma-separated).
- `frontend/src/components/AnalyticsView.tsx`: alignment and consistency show `–` when `null`, plus a one-line coverage note under the score table.

## 7. TDD checklist (write each failing first; use the `temp_db` fixture; 2-space indent in these files)

1. `task_key`: `"Wash clothes."`, `" wash  CLOTHES"` → same key.
2. Resolve: explicit link beats a matching cue; explicit `none` beats a cue; unique cue prefix matches; two goals matching one task → unreviewed; short cue (< 3 chars) is rejected on save.
3. Alignment worked example in §3.2 → 70.0 and coverage 20/24; under 5 reviewed completed tasks → `None`; unreviewed tasks do not move the score; a `none` task lowers it.
4. Consistency worked example in §4 → 55.0; `L < 7` → `None`; fewer than 5 wake times → rhythm only; days with no tasks are not solid; `morning_completed`/`evening_completed` have no effect.
5. Migration 8 creates the table and column; cascade on goal delete returns the key to the review queue.
6. API: review queue ordering, `PUT /tasks/links` changes the stored alignment, goal attention counts.
7. Existing tests that pin the old alignment/consistency behaviour (`tests/test_analytics.py` `TestGoalAlignment`, `TestConsistency`) are rewritten to the new rules, not deleted silently.

## 8. Rollout on the real data

1. Backup (`DataPortabilityService.create_backup()`), then start the API once so migration 8 applies.
2. User adds cues to the 8 goals, then clears the review queue (about 5 minutes for ~80 keys after cues).
3. Run `recompute_all_scores()`; check results with read-only SQL against `goalos.db`, not the script's printed summary (project rule). Expected: alignment is `None` for early windows until enough tasks are reviewed, then a real percentage; consistency in the 40s–60s.

## 9. ⚠ Assumptions to re-confirm with the user before or while implementing

1. Alignment counts only **completed** tasks, and chores (`none`) lower it.
2. 14-day window; minimum 5 reviewed completed tasks (alignment) and 7 logged days (consistency).
3. A "solid day" is ≥ 50% of tasks ticked, matching the calendar's task-rate rule. Weights 70/30; wake sd scale 0 h → 100, 2 h → 0.
4. The user writes cues by hand; matching is token-prefix; no suggestions in v1.
5. Links are by task text across all days (one decision applies to every occurrence).

## 10. Related findings, out of scope here (decide separately)

- `services/life_calendar_service.py` marks a day productive if `log.morning_completed and log.evening_completed`. The importer sets both for every imported day, so that clause makes every one of the 92 days "productive" on the calendar. Recommend removing that clause.
- Both 1-month goals (`Getting a job`, `Getting my body in shape`) have a deadline of 2026-08-31, which has passed. `gap_score` and the coach's monthly pacing read those. Renew or close them.
- `JournalImportService.parse_entry` stores `task_completion_rate` as a 0–1 fraction while the real import script stores a percent (0–100); the real data is all percent. Only the unused text/excel import path is affected.

## 11. Non-goals

LLM-assisted linking, linking PLAN hour-blocks to goals (a good follow-up: it would give hours per goal), changing `gap_score`/`momentum_score`/`learning_score`, per-day link overrides, and any change to how the journal is imported.
