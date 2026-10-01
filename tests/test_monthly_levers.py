"""Lever analysis: which habits move the day's task completion (associations on small samples)."""

import json
import random
from datetime import date, timedelta

from database.repositories.log_repository import LogRepository
from models.daily_log import DailyLogCreate
from services.monthly_analytics_service import MonthlyAnalyticsService
from services.monthly_levers import CAVEAT, build_focus, compute_levers, spearman, tier_for


def _row(i, rate, **fields):
  row = {
    "date": date(2026, 7, 1) + timedelta(days=i),
    "rate": rate,
    "n_tasks": 4,
    "done": None,
    "sleep": None,
    "wake": None,
    "bed_prev": None,
    "prev_rate": None,
    "plan_filled": None,
    "weekend": False,
    "tasks": [],
  }
  row.update(fields)
  return row


def _wake_effect_rows(n=60):
  """Later wake -> fewer tasks done, with small deterministic noise."""
  wakes = [6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5]
  rows = []
  for i in range(n):
    wake = wakes[i % 7]
    rate = min(100.0, max(0.0, 100 - 25 * (wake - 6.5) + ((i * 37) % 7 - 3)))
    rows.append(_row(i, rate, wake=wake))
  return rows


def _by_lever(result):
  return {f["lever"]: f for f in result["findings"]}


def test_spearman_handles_direction_ties_and_constants():
  assert spearman([1, 2, 3, 4], [10, 20, 30, 40]) == 1.0
  assert spearman([1, 2, 3, 4], [40, 30, 20, 10]) == -1.0
  assert spearman([1, 2, 2, 3], [1, 2, 2, 3]) == 1.0
  assert spearman([1, 1, 1], [1, 2, 3]) is None


def test_planted_wake_effect_is_found_with_n_groups_and_caveat():
  result = compute_levers(_wake_effect_rows(), seed=202609)
  finding = _by_lever(result)["wake"]
  assert finding["tier"] == "strong" and finding["n"] == 60 and finding["rho"] < -0.8
  early, late = finding["groups"]
  assert early["label"] == "wake by 07:30" and late["label"] == "wake 08:30 or later"
  assert early["mean"] > late["mean"] and early["n"] > 0 and late["n"] > 0
  assert "n=" in finding["contrast"] and finding["caveat"] == CAVEAT
  assert result["method_version"] == 1 and result["window_days"] == 60


def test_strong_needs_to_survive_correction_for_the_number_of_levers_tested():
  assert tier_for(0.006, tests=7) == "strong"  # 0.006 x 7 = 0.042
  assert tier_for(0.009, tests=7) == "suggestive"  # 0.063 after correction, but p < 0.05 on its own
  assert tier_for(0.046, tests=7) == "suggestive"
  assert tier_for(0.06, tests=7) is None
  assert tier_for(0.009, tests=1) == "strong"


def test_findings_report_how_many_levers_were_tested(planted=None):
  finding = _by_lever(compute_levers(_wake_effect_rows(), seed=202609))["wake"]
  assert finding["tests"] == 1 and finding["p_adjusted"] == finding["p"]  # only wake had data to test


def test_too_few_days_yields_no_finding():
  assert compute_levers(_wake_effect_rows(20), seed=1)["findings"] == []


def test_no_relationship_yields_no_finding():
  rng = random.Random(5)
  rows = [_row(i, rng.uniform(0, 100), wake=rng.choice([6.5, 7.5, 8.5, 9.5])) for i in range(80)]
  assert compute_levers(rows, seed=1)["findings"] == []


def test_results_are_deterministic_for_a_seed():
  rows = _wake_effect_rows()
  assert compute_levers(rows, seed=7) == compute_levers(rows, seed=7)


def test_sleep_finding_carries_the_wake_time_confound_note():
  rows = [{**r, "sleep": r["wake"] - 1.0} for r in _wake_effect_rows()]  # sleep moves in lockstep with wake time
  found = _by_lever(compute_levers(rows, seed=3))
  assert "wake" in found and "sleep" in found
  assert "wake time" in found["sleep"]["caveat"]


def test_plan_size_observation_reports_tasks_done_per_day():
  rows = [
    _row(0, 50.0, n_tasks=2, done=1), _row(1, 50.0, n_tasks=2, done=1), _row(2, 0.0, n_tasks=2, done=0),
    _row(3, 60.0, n_tasks=5, done=3), _row(4, 40.0, n_tasks=6, done=2),
  ]
  by_bucket = {b["bucket"]: b for b in compute_levers(rows, seed=1)["observations"]["plan_size"]}
  assert by_bucket["2 or fewer"] == {"bucket": "2 or fewer", "days": 3, "avg_planned": 2.0, "avg_done": 0.67}
  assert by_bucket["5+"] == {"bucket": "5+", "days": 2, "avg_planned": 5.5, "avg_done": 2.5}
  assert "3" not in by_bucket  # empty buckets are omitted


def test_task_position_observation_counts_done_by_list_position():
  rows = [_row(0, 50.0, tasks=[True, False]), _row(1, 50.0, tasks=[True, True, False, False, False, True])]
  pos = {p["position"]: p for p in compute_levers(rows, seed=1)["observations"]["task_position"]}
  assert (pos["1"]["done"], pos["1"]["total"], pos["1"]["rate"]) == (2, 2, 100.0)
  assert (pos["2"]["done"], pos["2"]["total"]) == (1, 2)
  assert (pos["5+"]["done"], pos["5+"]["total"]) == (1, 2)  # tasks 5 and 6 of day two


def test_focus_lines_come_from_findings_and_stuck_tasks():
  result = compute_levers(_wake_effect_rows(), seed=202609)
  stuck = [{"task": "Apply for 10 companies", "planned": 4, "done": 1}]
  lines = build_focus(result["findings"], stuck)
  assert any("07:30" in line and "%" in line for line in lines)
  assert any("Apply for 10 companies" in line and "4" in line for line in lines)
  assert build_focus([], []) == []


def test_snapshot_stores_levers_over_the_trailing_90_days(temp_db):
  repo = LogRepository()
  for i in range(60):  # Jul 1 .. Aug 29
    wake = [6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5][i % 7]
    done_count = round(4 * min(1.0, max(0.0, 1 - 0.25 * (wake - 6.5) / 1.0)))
    tasks = [{"text": f"t{j}", "completed": j < done_count} for j in range(4)]
    clock = f"{int(wake)}:{int((wake % 1) * 60):02d} AM - 12:00 AM"
    repo.create(DailyLogCreate(date=date(2026, 7, 1) + timedelta(days=i), awake_range=clock, planned_tasks=json.dumps(tasks)))
  snap = MonthlyAnalyticsService().recompute_month("2026-08", today=date(2026, 9, 5))
  assert snap.insights["method_version"] == 1
  assert snap.insights["window_days"] == 60  # everything up to Aug 29 fits inside 90 days
  assert any(f["lever"] == "wake" for f in snap.insights["findings"])
  assert snap.insights["focus"]  # at least the wake-time line
  # a facts-only recompute (used on every journal save) must not wipe stored insights
  facts_only = MonthlyAnalyticsService().recompute_month("2026-08", today=date(2026, 9, 5), with_insights=False)
  assert facts_only.insights == snap.insights
