"""Analytics service tests."""

from datetime import date, timedelta

from models.daily_log import DailyLog, DailyLogCreate
from models.goal import Goal, GoalCreate
from services.analytics_service import (
  consistency_score,
  gap_score,
  goal_alignment_score,
  health_score,
  learning_score,
  linear_regression_slope,
  momentum_score,
  normalize,
  overall_growth_score,
  productivity_score,
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


class TestGoalAlignment:
  def test_matching_tasks(self):
    goals = [_make_goal(title="Learn Python coding", reason="career growth")]
    tasks = ["Solve Python coding problems"]
    score = goal_alignment_score(tasks, goals)
    assert 0 <= score <= 100
    assert score > 0

  def test_empty_inputs(self):
    assert goal_alignment_score([], []) == 0.0
    assert goal_alignment_score(["task"], []) == 0.0


class TestConsistency:
  def test_empty_logs(self):
    assert consistency_score([]) == 0.0

  def test_full_streak(self):
    logs = [_make_log(date(2026, 6, 23) - timedelta(days=i), morning=True) for i in range(10)]
    score = consistency_score(logs)
    assert 0 < score <= 100

  def test_partial_completion(self):
    logs = [_make_log(date(2026, 6, 20) + timedelta(days=i), morning=(i % 2 == 0)) for i in range(10)]
    score = consistency_score(logs)
    assert 0 < score < 100


class TestHealth:
  def test_optimal(self):
    score = health_score(8.0, 5, True, 5)
    assert score >= 90

  def test_no_data(self):
    score = health_score(None, None, False, None)
    assert score == 0.0

  def test_workout_only(self):
    score = health_score(None, None, True, None)
    assert score == 30.0


class TestLearning:
  def test_keywords(self):
    score = learning_score("I studied coding and read a book", ["codekata practice"])
    assert score >= 40

  def test_empty(self):
    assert learning_score("", []) == 0.0


class TestProductivity:
  def test_high_productivity(self):
    score = productivity_score(5.0, 0.9, 5)
    assert score >= 80

  def test_zero(self):
    assert productivity_score(0, 0, 1) >= 0


class TestMomentum:
  def test_upward_trend(self):
    scores = [50, 55, 60, 65, 70, 75, 80]
    assert momentum_score(scores) > 50

  def test_flat(self):
    scores = [50.0] * 7
    assert momentum_score(scores) == 50.0

  def test_empty(self):
    assert momentum_score([]) == 50.0


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
    score = overall_growth_score(80, 80, 80, 80, 80, 80)
    assert score == 80.0

  def test_bounds(self):
    score = overall_growth_score(100, 100, 100, 100, 100, 100)
    assert score == 100.0

  def test_zero(self):
    score = overall_growth_score(0, 0, 0, 0, 0, 0)
    assert score == 0.0
