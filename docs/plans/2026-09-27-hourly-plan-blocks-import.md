# Plan: Normalize PLAN section into fixed hourly blocks on journal import

**Repo:** GoalOS (`c:\Users\jegad\projects\GoalOS`). Backend: FastAPI + SQLite + Pydantic v2.
**Primary file to change:** `services/journal_import_service.py`
**Also touch:** `models/import_result.py`, `tests/test_journal_import.py`

## Context

GoalOS imports the user's handwritten daily journal (photographed, transcribed to
text, then bulk-imported) via `JournalImportService`. Each day's transcript has
six sections, in this exact order, confirmed as the user's permanent standard
starting 2026-07-01 (all data before that date has been deleted from the DB —
don't worry about back-compat with anything older):

```
DD/M/YY

GRATITUDE
<one sentence>

AWAKE
<start time> - <end time>.        e.g. "9:00 AM - 12.30 AM."

PLAN
<start>-<end> <activity>          one line per block, times often bare numbers
<start>-<end> <activity>          with no AM/PM marker, e.g. "9-10", "1-3"

TASKS
① <task text> <✓ or X>            circled-digit or "N." numbering; ✓/X/[done] = done
② <task text>

REVIEW
<paragraph>

TAKEAWAY
<one sentence>
```

The AWAKE section was already wired up this session: `_parse_awake_range()`
in `journal_import_service.py` parses `"9:00 AM - 12.30 AM."` into
`awake_range="9:00 AM - 12.30 AM"` and `sleep_hours=8.5`, storing both on
`DailyLogCreate`. Read that function first — this plan builds directly on it
and reuses its `AWAKE_TIME` regex.

## The problem this plan solves

`_parse_plans()` currently stores each PLAN line **as written**, with whatever
width the user happened to use that day (30 min, 1h, 3h, whatever). That means
"what was I doing around 3pm" is not comparable day-to-day — the blocks aren't
aligned to anything. The user wants every day's PLAN normalized into a fixed
grid of **1-hour blocks**, spanning their actual awake window, so 6 months of
data become directly comparable hour-by-hour.

Concretely: if the user writes `"6-9 met my friends"` (one line, a 3-hour
span), it must become **three separate 1-hour blocks** — `6-7`, `7-8`, `8-9`
— each with the identical activity text `"met my friends"`. Hours with
nothing written stay empty.

## The hard part: resolving bare hour numbers

The user's real notebook writes PLAN times as bare numbers with no AM/PM,
e.g. this real sequence for a day that started at 9:00 AM:

```
9-10   Wakeup, shower, breakfast, job application
10-11  Tea time break, applications
11-12  applications, chill
12-1   lunch and youtube
1-3    chess and networking
3-4    chill
4-7    timewasted
7-8    dinner & youtube
8-12   time waste
```

A human reads this as continuing forward through the day (12→1 means noon→1pm,
not 1am), never wrapping backward. You must reproduce that reading
algorithmically — **do not** naively treat `1` as `1:00` (which would place it
before wake time). The rule: maintain a running "current absolute hour"
starting at the wake hour (from AWAKE), and for each written block, resolve
its bare start/end numbers to whichever of `{n, n+12}` keeps the timeline
moving forward (monotonically non-decreasing from the previous block's
resolved end).

**Worked reference example** (wake = 9.0, i.e. "9:00 AM"), used as a test case:

| written | resolved (24h decimal) |
|---|---|
| 9-10 | 9.0 – 10.0 |
| 10-11 | 10.0 – 11.0 |
| 11-12 | 11.0 – 12.0 |
| 12-1 | 12.0 – 13.0 |
| 1-3 | 13.0 – 15.0 |
| 3-4 | 15.0 – 16.0 |
| 4-7 | 16.0 – 19.0 |
| 7-8 | 19.0 – 20.0 |
| 8-12 | 20.0 – 24.0 |

Algorithm per block, given `prev_end_abs` (starts at `wake_hour`):
```
def resolve(n, prev_end_abs):
    candidates = [n, n + 12]
    # pick the smallest candidate that is >= prev_end_abs;
    # if neither qualifies (shouldn't happen with well-formed input), pick the larger
    valid = [c for c in candidates if c >= prev_end_abs]
    return min(valid) if valid else max(candidates)

start_abs = resolve(start_n, prev_end_abs)
end_abs   = resolve(end_n, start_abs)
prev_end_abs = end_abs
```
Times already containing `:` (e.g. `10:30`) parse as `hour + minute/60` before
resolution; the resolve step still applies to the hour part.

## Grid boundaries

- **Start:** `ceil(wake_hour)` — 9:00 AM → grid starts at 9; 9:30 AM → grid
  starts at 10 (the 9-10 hour is not tracked since they weren't awake for
  most of it).
- **End:** **midnight (24.0), always** — regardless of the literal AWAKE end
  time. The user confirmed via example: awake until 1:00 AM still produces a
  last block of `23:00–24:00` (11pm–12am), not a `24:00–25:00` block. The
  stretch between midnight and actual sleep is not tracked as blocks at all.
- Every integer hour in `[start, 24)` gets exactly one block. If no resolved
  PLAN range covers that hour, its `activity` is `""` (empty string, not
  null, not a placeholder — consistent with "missing = empty" everywhere
  else in this pipeline).
- If a day has **no AWAKE section** (so no wake hour to anchor the grid),
  fall back to storing the raw, unsplit blocks from `_parse_plans()` as
  today — do not silently drop PLAN data just because AWAKE was skipped.

⚠️ **This midnight-cap end rule was inferred from one example the user gave,
not stated as an explicit universal rule. Before merging, re-confirm with
the user: "grid always ends at midnight regardless of actual sleep time —
correct?"** If they say no, the end rule needs to change; everything else in
this plan is independent of that answer.

## What NOT to guess (carry-forward from earlier this session)

This whole import pipeline was just audited and cleaned of fabricated data
(see `.agents/brain/evolution_log.md`, 2026-09-27 entries, and the now-deleted
`extract_sleep_hours`/`extract_mood`/`extract_deep_work_hours` heuristics in
`scripts/backfill_analytics.py`). Do not reintroduce guessing here:
- No AWAKE section → no grid, fall back to raw blocks (above). Don't assume a
  wake time.
- Unparseable/ambiguous PLAN line → keep it out of the grid rather than
  guessing which hour it belongs to; log/skip it, don't silently drop other
  valid blocks in the same day.
- Empty hour → `""`, never a fabricated activity.

## Implementation

### 1. `models/import_result.py`
No new fields needed on `ParsedEntry` — the hourly grid replaces the contents
of the existing `plans: list[ParsedTimeBlock]`, same shape (`start`, `end`,
`activity`), just normalized to 1-hour widths. `ParsedTimeBlock.start`/`end`
can stay strings; use `"9"`, `"10"` etc. (zero-padding optional, but be
consistent — check how `frontend/src/components/JournalView.tsx`'s
`parseTimeBlocks`/time-block editor expects `start`/`end` to look before
picking a format, since that UI reads this same `time_blocks` JSON when a
user opens an imported day to edit it).

### 2. `services/journal_import_service.py`
- Add a time-token parser (hour + optional `:MM`, no AM/PM) returning a bare
  float hour, e.g. `_parse_bare_hour("10:30") -> 10.5`.
- Add the `resolve()` forward-carry logic above as a helper, e.g.
  `_resolve_plan_times(plans: list[ParsedTimeBlock], wake_hour: float) -> list[tuple[float, float, str]]`
  returning `(start_abs, end_abs, activity)` triples.
- Add `_build_hourly_blocks(resolved: list[tuple[float,float,str]], wake_hour: float) -> list[ParsedTimeBlock]`
  implementing the grid-boundary rules above, returning one `ParsedTimeBlock`
  per hour from `ceil(wake_hour)` to `24`.
- Wire into `parse_entry()`: after computing `plans` (existing raw parse) and
  `awake_range`/`sleep_hours` (existing), if a wake hour is available, replace
  `plans` with the hourly-normalized version before building `ParsedEntry`.
  You'll need the wake hour as a float, not just the `awake_range` display
  string — extend `_parse_awake_range` (or add a sibling) to also return it,
  reusing the existing `AWAKE_TIME` regex.
- `store_entry()` needs no changes — it already serializes `entry.plans` to
  `time_blocks_json` as-is.

### 3. Tests — `tests/test_journal_import.py`
Follow the existing style in that file (`TestJournalImport` class, `temp_db`
fixture). Add at minimum:
- A test reproducing the worked reference example above end-to-end (wake
  9:00 AM, the 9-line PLAN block from the real notebook page), asserting the
  final `entry.plans` has exactly 15 entries (hours 9 through 23 inclusive,
  i.e. `24 - 9 = 15` one-hour blocks), each with the correct `start`/`end`/
  `activity`, matching the resolved table above.
- A test for the multi-hour-repeat case: `"6-9 met my friends"` with some
  wake hour ≤ 6 → produces 3 blocks (`6-7`, `7-8`, `8-9`), all with
  `activity == "met my friends"`.
- A test for an empty gap hour: a PLAN with a hole (e.g. blocks covering
  9-10 and 11-12 but nothing for 10-11) → the 10-11 block exists with
  `activity == ""`.
- A test for **no AWAKE section present**: PLAN still parses, but falls back
  to the old unsplit behavior (don't fabricate a wake time).
- Run the full suite after: `python -m pytest -q` (139 passing before this
  change — should be 139 + new tests, all green) and `python -m ruff check .`
  (must stay clean).

## Explicitly out of scope for this change

- `scripts/import_journal_csv.py` (a separate, older importer for a specific
  spreadsheet file) — do not touch unless separately asked.
- The live in-app Journal page's manual time-block editor
  (`frontend/src/components/JournalView.tsx`) — no frontend changes planned;
  just confirm visually afterward that it still renders/edits an imported
  day's hourly blocks reasonably (many small rows instead of few wide ones
  is expected and fine).
- Deriving `deep_work_hours` from the new hourly blocks — not asked for,
  don't add it speculatively.
