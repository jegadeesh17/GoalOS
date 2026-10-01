"""Monthly snapshot facts: counts, sleep/schedule, goals, provisional vs final."""

import json
from datetime import date

from database.connection import get_db
from database.repositories.goal_repository import GoalRepository
from database.repositories.log_repository import LogRepository
from database.repositories.score_repository import ScoreRepository
from models.daily_log import DailyLogCreate
from models.goal import GoalCreate, GoalUpdate
from models.score import ScoreCreate
from services.journal_helpers import task_key
from services.monthly_analytics_service import MonthlyAnalyticsService


def _tasks(*done_flags: bool, names: list[str] | None = None) -> str:
  names = names or [f"task {i}" for i in range(len(done_flags))]
  return json.dumps([{"text": n, "completed": d} for n, d in zip(names, done_flags, strict=True)])


def _log(day: date, awake=None, sleep=None, tasks: str | None = None, blocks: list[str] | None = None, **extra):
  time_blocks = None
  if blocks is not None:
    time_blocks = json.dumps([{"start": str(9 + i), "end": str(10 + i), "activity": a} for i, a in enumerate(blocks)])
  LogRepository().create(
    DailyLogCreate(date=day, awake_range=awake, sleep_hours=sleep, planned_tasks=tasks, time_blocks=time_blocks, **extra)
  )


def _goal(**fields):
  goal = GoalRepository().create(GoalCreate(**fields))
  with get_db() as conn:
    conn.execute("UPDATE goals SET created_at = '2026-08-01 08:00:00' WHERE id = ?", (goal.id,))
  return goal


def _seed_september():
  _log(date(2026, 9, 1), "8:00 AM - 1:00 AM", 7.0, _tasks(True, True, False, False), ["gym", "code", ""])
  _log(date(2026, 9, 2), "9:00 AM - 2:00 AM", 8.0, _tasks(True, True, True))
  _log(date(2026, 9, 3), "7:00 AM - 11:00 PM", 5.5, _tasks(False, False))
  _log(date(2026, 9, 5), "8:00 AM - 12:00 AM", None, None)  # 09-04 missing -> sleep unknown


def test_task_key_normalises_case_punctuation_and_spacing():
  assert task_key("Wash clothes.") == task_key(" wash  CLOTHES") == "wash clothes"


def test_month_facts_match_hand_computation(temp_db):
  _seed_september()
  snap = MonthlyAnalyticsService().recompute_month("2026-09", today=date(2026, 9, 20))
  m = snap.metrics
  assert (m["days_in_month"], m["days_logged"]) == (30, 4)
  t = m["tasks"]
  assert (t["planned"], t["done"]) == (9, 5)
  assert t["completion_rate"] == 55.6
  assert t["per_day"] == 2.25
  assert (t["solid_days"], t["zero_days"]) == (2, 1)  # 09-05 has no tasks, so it is neither
  s = m["sleep"]
  assert (s["nights_known"], s["avg_hours"], s["under_6"], s["at_least_7"]) == (3, 6.83, 1, 2)
  assert s["wake"]["avg_clock"] == "08:00" and s["wake"]["n"] == 4 and s["wake"]["sd"] == 0.71
  assert s["bedtime"]["avg_clock"] == "00:30" and s["bedtime"]["n"] == 4 and s["bedtime"]["excluded"] == 0
  assert m["sleep"]["unknown_reasons"] == {"no_previous_day": 1}
  assert m["plan"] == {"avg_hours_filled": 2.0, "n": 1}


def test_implausible_bedtimes_are_excluded_not_averaged(temp_db):
  _log(date(2026, 9, 1), "8:30 AM - 11:00 AM", None, None)  # 2.5h awake window: a slip, not a bedtime
  _log(date(2026, 9, 2), "8:00 AM - 12:00 AM", None, None)
  m = MonthlyAnalyticsService().recompute_month("2026-09", today=date(2026, 9, 20)).metrics
  assert m["sleep"]["bedtime"]["n"] == 1 and m["sleep"]["bedtime"]["excluded"] == 1
  assert m["sleep"]["bedtime"]["avg_clock"] == "00:00"
  assert m["sleep"]["unknown_reasons"] == {"no_previous_day": 1, "implausible_bedtime": 1}  # 09-02: yesterday's bedtime unusable


def test_provisional_until_the_month_is_over_and_fully_imported(temp_db):
  _seed_september()
  svc = MonthlyAnalyticsService()
  assert svc.recompute_month("2026-09", today=date(2026, 9, 20)).status == "provisional"
  # month is over but the last logged day is the 5th: the import is incomplete
  late = svc.recompute_month("2026-09", today=date(2026, 10, 2))
  assert late.status == "provisional" and late.data_through == date(2026, 9, 5)
  _log(date(2026, 9, 30), "8:00 AM - 1:00 AM", None, None)
  assert svc.recompute_month("2026-09", today=date(2026, 10, 2)).status == "final"


def test_recompute_is_idempotent_and_persisted(temp_db):
  _seed_september()
  svc = MonthlyAnalyticsService()
  first = svc.recompute_month("2026-09", today=date(2026, 9, 20))
  second = svc.recompute_month("2026-09", today=date(2026, 9, 20))
  assert first.metrics == second.metrics
  assert [s.month for s in svc.list_snapshots()] == ["2026-09"]
  assert svc.get_snapshot("2026-09").metrics == first.metrics


def test_month_without_logs_stores_nothing(temp_db):
  svc = MonthlyAnalyticsService()
  assert svc.recompute_month("2026-08", today=date(2026, 9, 1)) is None
  assert svc.list_snapshots() == []


def test_recompute_all_covers_every_month_with_logs(temp_db):
  _log(date(2026, 8, 31), "8:00 AM - 1:00 AM", None, _tasks(True))
  _seed_september()
  months = [s.month for s in MonthlyAnalyticsService().recompute_all(today=date(2026, 10, 2))]
  assert months == ["2026-08", "2026-09"]


def test_delta_vs_previous_month(temp_db):
  _log(date(2026, 8, 31), "8:00 AM - 1:00 AM", 7.0, _tasks(True, False))  # Aug: 50%
  _seed_september()  # Sep: 55.6%
  m = MonthlyAnalyticsService().recompute_month("2026-09", today=date(2026, 9, 20)).metrics
  assert m["delta_vs_previous"]["completion_rate"] == 5.6
  assert m["delta_vs_previous"]["avg_sleep_hours"] == -0.17  # 6.83 - 7.00


def test_first_month_has_no_deltas(temp_db):
  _seed_september()
  m = MonthlyAnalyticsService().recompute_month("2026-09", today=date(2026, 9, 20)).metrics
  assert m["delta_vs_previous"] == {}


def test_score_means_skip_unknown_values(temp_db):
  _seed_september()
  repo = ScoreRepository()
  repo.create(ScoreCreate(date=date(2026, 9, 1), scope="daily", overall_growth_score=40.0, health_score=None))
  repo.create(ScoreCreate(date=date(2026, 9, 2), scope="daily", overall_growth_score=60.0, health_score=80.0))
  sc = MonthlyAnalyticsService().recompute_month("2026-09", today=date(2026, 9, 20)).metrics["scores"]
  assert sc["overall"] == 50.0 and sc["health"] == 80.0
  assert sc["goal_alignment"] is None  # never scored -> unknown, not zero


def test_stuck_tasks_are_repeated_and_mostly_not_done(temp_db):
  for day, done in ((1, False), (2, False), (3, True), (4, False)):
    _log(date(2026, 9, day), None, None, _tasks(done, names=["Apply for 10 companies"]))
  _log(date(2026, 9, 5), None, None, _tasks(False, names=["Write report"]))
  _log(date(2026, 9, 6), None, None, _tasks(False, names=["Write report"]))
  m = MonthlyAnalyticsService().recompute_month("2026-09", today=date(2026, 9, 20)).metrics
  assert m["stuck_tasks"] == [{"task": "Apply for 10 companies", "planned": 4, "done": 1}]  # 2x is not enough


def test_weekly_series_uses_monday_weeks(temp_db):
  _seed_september()  # Sep 1 2026 is a Tuesday; Sep 5 a Saturday: all one Mon-Sun week
  weekly = MonthlyAnalyticsService().recompute_month("2026-09", today=date(2026, 9, 20)).metrics["tasks"]["weekly"]
  assert weekly == [{"week_start": "2026-08-31", "planned": 9, "done": 5, "rate": 55.6}]


def test_goal_results_refresh_while_provisional_then_freeze_once_final(temp_db):
  goal = _goal(title="Getting a job", category="career", horizon="1-month", progress=0.1)
  svc = MonthlyAnalyticsService()
  _seed_september()
  _log(date(2026, 9, 30), "8:00 AM - 1:00 AM", None, None)
  svc.recompute_month("2026-09", today=date(2026, 9, 30))  # the month is still current: provisional
  [row] = svc.get_goal_results("2026-09")
  assert (row.goal_id, row.goal_title, row.progress_at_close, row.as_of) == (goal.id, "Getting a job", 0.1, date(2026, 9, 30))
  GoalRepository().update(goal.id, GoalUpdate(progress=0.3))
  svc.recompute_month("2026-09", today=date(2026, 9, 30))  # still provisional: refreshed
  assert svc.get_goal_results("2026-09")[0].progress_at_close == 0.3
  assert svc.recompute_month("2026-09", today=date(2026, 10, 2)).status == "final"
  GoalRepository().update(goal.id, GoalUpdate(title="Renamed", progress=0.9))
  svc.recompute_month("2026-09", today=date(2026, 10, 20))  # final: history must not be rewritten
  [row] = svc.get_goal_results("2026-09")
  assert row.goal_title == "Getting a job" and row.progress_at_close == 0.3 and row.as_of == date(2026, 9, 30)


def test_no_goal_results_are_invented_for_old_months(temp_db):
  GoalRepository().create(GoalCreate(title="Getting a job", category="career", horizon="1-month"))
  _log(date(2026, 7, 3), None, None, _tasks(True))
  MonthlyAnalyticsService().recompute_month("2026-07", today=date(2026, 10, 2))
  assert MonthlyAnalyticsService().get_goal_results("2026-07") == []
