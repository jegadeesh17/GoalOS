"""Analytics service tests."""

import json
from datetime import date

import pytest

from database.repositories.score_repository import ScoreRepository
from models.daily_log import DailyLog, DailyLogCreate
from models.goal import Goal, GoalCreate
from models.score import ScoreCreate
from services.analytics_service import (
  calculate_daily_scores,
  gap_score,
  health_score,
  linear_regression_slope,
  momentum_score,
  normalize,
  overall_growth_score,
  productivity_score,
  recent_overall_scores,
)


def _make_log(d: date, morning=False, evening=False, **kwargs) -> DailyLog:
  data = DailyLogCreate(date=d, morning_completed=morning, evening_completed=evening, **kwargs)
  return DailyLog(id=1, **data.model_dump())


def _make_goal(**kwargs) -> Goal:
  defaults = {"title": "Test Goal", "category": "career", "horizon": "yearly"}
  defaults.update(kwargs)
  data = GoalCreate(**defaults)
  return Goal(id=1, **data.model_dump())


class TestNormalize:
  def test_mid_value(self):
    assert normalize(6.5, 4, 9) == 0.5

  def test_below_min(self):
    assert normalize(2, 4, 9) == 0.0

  def test_above_max(self):
    assert normalize(10, 4, 9) == 1.0

  def test_none(self):
    assert normalize(None, 0, 10) == 0.0


class TestHealth:
  def test_optimal(self):
    score = health_score(8.0, 5, True, 5)
    assert score >= 90

  def test_no_data(self):
    score = health_score(None, None, False, None)
    assert score == 0.0

  def test_all_missing_is_unknown_not_zero(self):
    assert health_score(None, None, None, None) is None

  def test_workout_only_scores_just_the_workout(self):
    assert health_score(None, None, True, None) == 100.0
    assert health_score(None, None, False, None) == 0.0

  def test_sleep_only_is_not_capped_by_missing_inputs(self):
    # 8.5h is 90% of the 4-9h sleep range; workout/energy were never recorded.
    assert health_score(8.5, None, None, None) == 90.0


class TestProductivity:
  def test_high_productivity(self):
    score = productivity_score(5.0, 0.9, 5)
    assert score >= 80

  def test_zero(self):
    assert productivity_score(0, 0, 1) >= 0

  def test_all_missing_is_unknown_not_zero(self):
    assert productivity_score(None, None, None) is None

  def test_task_rate_only_scores_the_rate(self):
    assert productivity_score(None, 0.5, None) == 50.0
    assert productivity_score(None, 1.0, None) == 100.0
    assert productivity_score(None, 0.0, None) == 0.0

  def test_missing_parts_are_left_out_not_zeroed(self):
    # deep work (50 pts) at 3 of 6 h plus tasks (30 pts) at 100% -> 55 of 80 -> 68.75
    assert productivity_score(3.0, 1.0, None) == 68.75


class TestMomentum:
  def test_upward_trend(self):
    scores = [50, 55, 60, 65, 70, 75, 80]
    assert momentum_score(scores) > 50

  def test_flat(self):
    scores = [50.0] * 7
    assert momentum_score(scores) == 50.0

  def test_no_history_is_unknown_not_neutral(self):
    assert momentum_score([]) is None

  def test_too_little_history_is_unknown(self):
    assert momentum_score([50.0, 60.0, 70.0, 80.0]) is None
    assert momentum_score([50.0, 60.0, 70.0, 80.0, 90.0]) is not None


class TestLinearRegression:
  def test_positive_slope(self):
    assert linear_regression_slope([1, 2, 3, 4, 5]) > 0

  def test_single_value(self):
    assert linear_regression_slope([5]) == 0.0


class TestGapScore:
  def test_no_goals(self):
    assert gap_score([], []) == 100.0

  def test_behind_pace(self):
    goal = _make_goal(progress=0.1, deadline=date(2026, 12, 31))
    goal.created_at = date(2026, 1, 1)
    from datetime import datetime
    goal = Goal(
      id=1, title="G", category="c", horizon="y", progress=0.1,
      deadline=date(2026, 12, 31), created_at=datetime(2026, 1, 1),
    )
    score = gap_score([goal], [], today=date(2026, 6, 1))
    assert 0 <= score <= 100


class TestOverallGrowth:
  def test_weighted_average(self):
    score = overall_growth_score(80, 80, 80, 80, 80)
    assert score == 80.0

  def test_bounds(self):
    score = overall_growth_score(100, 100, 100, 100, 100)
    assert score == 100.0

  def test_zero(self):
    score = overall_growth_score(0, 0, 0, 0, 0)
    assert score == 0.0

  def test_unknown_components_are_left_out_and_weights_renormalised(self):
    assert overall_growth_score(80, 80, None, 80, 80) == pytest.approx(80.0)
    # goal 0.30*100 + consistency 0.25*0 over their combined weight 0.55
    assert round(overall_growth_score(100, 0, None, None, None), 4) == round(30 / 55 * 100, 4)

  def test_everything_unknown(self):
    assert overall_growth_score(None, None, None, None, None) is None


class TestDailyScoresFromRealFields:
  def test_percent_task_rate_drives_productivity_and_missing_fields_are_ignored(self, temp_db):
    # task_completion_rate is stored as a percent (0-100); sleep_hours present, nothing else.
    log = _make_log(date(2026, 9, 20), evening=True, task_completion_rate=50.0, sleep_hours=8.5)
    score = calculate_daily_scores(log, [], [log], [])
    assert score.productivity_score == 50.0
    assert score.health_score == 90.0

  def test_task_rate_comes_from_the_task_list_not_a_fraction_saved_by_the_editor(self, temp_db):
    # The Journal editor autosaves task_completion_rate as a 0-1 fraction; the task list is authoritative.
    tasks = json.dumps([{"text": "a", "completed": True}, {"text": "b", "completed": False}])
    log = _make_log(date(2026, 9, 22), evening=True, planned_tasks=tasks, task_completion_rate=0.5)
    assert calculate_daily_scores(log, [], [log], []).productivity_score == 50.0

  def test_unknown_inputs_are_stored_as_null_not_zero(self, temp_db):
    log = _make_log(date(2026, 9, 21), evening=True)
    score = calculate_daily_scores(log, [], [log], [])
    assert score.productivity_score is None
    assert score.health_score is None
    # No keyword guessing and no neutral filler: both stay unknown without data.
    assert score.learning_score is None
    assert score.momentum_score is None


class TestRecentOverallScores:
  def test_only_scores_before_the_date_oldest_first(self, temp_db):
    repo = ScoreRepository()
    for day in range(1, 11):
      repo.create(ScoreCreate(date=date(2026, 9, day), scope="daily", overall_growth_score=float(day * 10)))
    # Scoring Sept 8 must see Sept 1-7 (oldest first), never Sept 8-10 or the newest 7 overall.
    assert recent_overall_scores(date(2026, 9, 8)) == [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0]
    assert momentum_score(recent_overall_scores(date(2026, 9, 8))) > 50

  def test_skips_unknown_overall_scores(self, temp_db):
    repo = ScoreRepository()
    repo.create(ScoreCreate(date=date(2026, 9, 1), scope="daily", overall_growth_score=40.0))
    repo.create(ScoreCreate(date=date(2026, 9, 2), scope="daily", overall_growth_score=None))
    assert recent_overall_scores(date(2026, 9, 3)) == [40.0]
