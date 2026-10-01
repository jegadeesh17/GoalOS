"""Goal alignment and consistency, rewritten from word overlap / row-exists to links and rhythm."""

import json
from datetime import date, timedelta

import pytest

from database.repositories.goal_repository import GoalRepository
from database.repositories.log_repository import LogRepository
from database.repositories.score_repository import ScoreRepository
from models.daily_log import DailyLog, DailyLogCreate
from models.goal import GoalCreate
from services.analytics_service import (
  calculate_daily_scores,
  consistency_score,
  goal_alignment_score,
  recompute_all_scores,
  window_logs,
)
from services.task_link_service import NO_GOAL, UNREVIEWED, Resolution, TaskLinkService

DAY = date(2026, 9, 14)
GOAL = Resolution("goal", 1)


def _log(day: date, done=(), undone=(), awake=None, **kwargs) -> DailyLog:
  tasks = [{"text": t, "completed": True} for t in done] + [{"text": t, "completed": False} for t in undone]
  data = DailyLogCreate(date=day, planned_tasks=json.dumps(tasks) if tasks else None, awake_range=awake, **kwargs)
  return DailyLog(id=1, **data.model_dump())


def _resolver(mapping: dict):
  return lambda text: mapping.get(text, UNREVIEWED)


class TestGoalAlignment:
  def test_worked_example_14_of_20_reviewed_is_70_percent(self):
    logs = [
      _log(DAY, done=[f"job {i}" for i in range(8)]),
      _log(DAY - timedelta(days=1), done=[f"job {i}" for i in range(8, 14)] + [f"chore {i}" for i in range(6)]),
      _log(DAY - timedelta(days=2), done=[f"mystery {i}" for i in range(4)]),
    ]
    resolve = _resolver({**{f"job {i}": GOAL for i in range(14)}, **{f"chore {i}": NO_GOAL for i in range(6)}})
    result = goal_alignment_score(logs, resolve)
    assert result.score == 70.0
    assert (result.reviewed, result.completed) == (20, 24)
    assert result.coverage == pytest.approx(20 / 24)

  def test_unreviewed_tasks_do_not_move_the_score(self):
    base = [_log(DAY, done=["a", "b", "c", "d", "e"])]
    resolve = _resolver({"a": GOAL, "b": GOAL, "c": GOAL, "d": NO_GOAL, "e": NO_GOAL})
    padded = base + [_log(DAY - timedelta(days=1), done=[f"unknown {i}" for i in range(10)])]
    assert goal_alignment_score(base, resolve).score == goal_alignment_score(padded, resolve).score == 60.0

  def test_a_reviewed_chore_lowers_the_score(self):
    logs = [_log(DAY, done=["a", "b", "c", "d", "e"])]
    all_goal = _resolver({k: GOAL for k in "abcde"})
    one_chore = _resolver({**{k: GOAL for k in "abcd"}, "e": NO_GOAL})
    assert goal_alignment_score(logs, all_goal).score == 100.0
    assert goal_alignment_score(logs, one_chore).score == 80.0

  def test_under_five_reviewed_completed_tasks_is_unknown(self):
    logs = [_log(DAY, done=["a", "b", "c", "d"])]
    result = goal_alignment_score(logs, _resolver({k: GOAL for k in "abcd"}))
    assert result.score is None and result.reviewed == 4

  def test_tasks_that_were_not_completed_are_ignored(self):
    logs = [_log(DAY, done=["a", "b", "c", "d", "e"], undone=["x", "y", "z"])]
    result = goal_alignment_score(logs, _resolver({k: GOAL for k in "abcde"}))
    assert result.score == 100.0 and result.completed == 5

  def test_no_logs_or_no_task_list_is_unknown(self):
    assert goal_alignment_score([], _resolver({})).score is None
    result = goal_alignment_score([_log(DAY)], _resolver({}))
    assert result.score is None and result.coverage is None


def _window(solid: int, total: int = 14, wake_hours=None) -> list[DailyLog]:
  """`total` consecutive days ending at DAY; the first `solid` are 1-of-2 ticked, the rest 0-of-2."""
  logs = []
  for i in range(total):
    awake = None
    if wake_hours is not None:
      awake = f"{wake_hours[i % len(wake_hours)]}:00 AM - 11:00 PM"
    done, undone = (["x"], ["y"]) if i < solid else ([], ["x", "y"])
    logs.append(_log(DAY - timedelta(days=i), done=done, undone=undone, awake=awake))
  return logs


class TestConsistency:
  def test_worked_example_rhythm_and_wake_regularity(self):
    # 8 of 14 days solid (57.14), wake alternating 6 and 8 AM -> sd 1.0 h -> regularity 50
    assert consistency_score(_window(solid=8, wake_hours=[6, 8])) == pytest.approx(55.0)

  def test_fewer_than_seven_logged_days_is_unknown(self):
    assert consistency_score(_window(solid=6, total=6, wake_hours=[6, 8])) is None
    assert consistency_score([]) is None

  def test_fewer_than_five_wake_times_leaves_rhythm_only(self):
    assert consistency_score(_window(solid=7)) == pytest.approx(50.0)  # no wake times at all
    some = _window(solid=7)
    for i in range(4):
      some[i] = _log(some[i].date, done=["x"], undone=["y"], awake="6:00 AM - 11:00 PM")
    assert consistency_score(some) == pytest.approx(50.0)  # four is still too few

  def test_identical_wake_times_are_fully_regular_and_a_two_hour_spread_scores_zero(self):
    assert consistency_score(_window(solid=14, wake_hours=[6])) == pytest.approx(100.0)
    assert consistency_score(_window(solid=14, wake_hours=[5, 9])) == pytest.approx(70.0)  # sd 2.0 h -> regularity 0

  def test_a_day_without_tasks_is_not_solid(self):
    assert consistency_score([_log(DAY - timedelta(days=i)) for i in range(10)]) == 0.0

  def test_half_of_the_tasks_ticked_is_solid(self):
    assert consistency_score([_log(DAY - timedelta(days=i), done=["x"], undone=["y"]) for i in range(7)]) == 100.0

  def test_morning_and_evening_flags_have_no_effect(self):
    flagged = [
      _log(DAY - timedelta(days=i), undone=["x"], morning_completed=True, evening_completed=True) for i in range(10)
    ]
    assert consistency_score(flagged) == 0.0

  def test_the_window_is_the_14_days_ending_on_the_day(self):
    logs = _window(solid=0, total=7) + [_log(DAY - timedelta(days=20 + i), done=["x"]) for i in range(10)]
    in_window = window_logs(logs, DAY)
    assert len(in_window) == 7 and consistency_score(in_window) == 0.0
    assert len(window_logs(logs, DAY, days=14)) == 7
    assert [log.date for log in window_logs(_window(solid=0, total=20), DAY)] == [DAY - timedelta(days=i) for i in range(14)]


def _seed_week() -> None:
  tasks = [
    {"text": "Apply", "completed": True},
    {"text": "Wash clothes", "completed": True},
    {"text": "z", "completed": False},
  ]
  for i in range(7):
    LogRepository().create(DailyLogCreate(date=date(2026, 9, 1) + timedelta(days=i), planned_tasks=json.dumps(tasks)))


class TestDailyScoresUseLinks:
  def test_stored_scores_follow_cues_and_links(self, temp_db):
    GoalRepository().create(GoalCreate(title="Job", category="career", horizon="1-year", cues=["appl"]))
    _seed_week()
    assert recompute_all_scores() == 7
    last = ScoreRepository().get_by_date(date(2026, 9, 7))
    # "Wash clothes" is unreviewed, so every reviewed completed task serves the goal; 2 of 3 ticked is a solid day
    assert last.goal_alignment_score == 100.0 and last.consistency_score == 100.0
    early = ScoreRepository().get_by_date(date(2026, 9, 3))
    assert early.goal_alignment_score is None and early.consistency_score is None  # 3 reviewed < 5, 3 days < 7
    TaskLinkService().set_link("Wash clothes", "none", None)
    recompute_all_scores()
    assert ScoreRepository().get_by_date(date(2026, 9, 7)).goal_alignment_score == 50.0

  def test_recomputing_from_a_date_leaves_earlier_days_alone(self, temp_db):
    for i in range(3):
      LogRepository().create(DailyLogCreate(date=date(2026, 9, 1) + timedelta(days=i), planned_tasks="[]"))
    assert recompute_all_scores(since=date(2026, 9, 2)) == 2
    assert ScoreRepository().get_by_date(date(2026, 9, 1)) is None

  def test_calculate_daily_scores_accepts_a_resolver(self, temp_db):
    task = json.dumps([{"text": "a", "completed": True}])
    log = LogRepository().create(DailyLogCreate(date=DAY, planned_tasks=task))
    score = calculate_daily_scores(log, [], [log], [], resolve=_resolver({}))
    assert score.goal_alignment_score is None and score.consistency_score is None
