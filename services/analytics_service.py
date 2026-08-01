"""Deterministic score calculations — no AI."""

import re
from datetime import date, timedelta
from typing import Optional

from models.daily_log import DailyLog
from models.goal import Goal
from models.score import Score

LEARNING_KEYWORDS = [
  "read", "studied", "learned", "practiced", "course", "book",
  "research", "codekata", "coding",
]


def normalize(value: Optional[float], min_val: float, max_val: float) -> float:
  """Clamp and normalize value to 0-1 range."""
  if value is None:
    return 0.0
  if max_val == min_val:
    return 0.0
  clamped = max(min_val, min(max_val, value))
  return (clamped - min_val) / (max_val - min_val)


def _tokenize(text: str) -> set[str]:
  return set(re.findall(r"[a-zA-Z]{3,}", text.lower()))


def _text_similarity(text_a: str, text_b: str) -> float:
  """Keyword overlap similarity (0-1) as embedding proxy."""
  if not text_a or not text_b:
    return 0.0
  tokens_a = _tokenize(text_a)
  tokens_b = _tokenize(text_b)
  if not tokens_a or not tokens_b:
    return 0.0
  intersection = tokens_a & tokens_b
  union = tokens_a | tokens_b
  return len(intersection) / len(union)


def goal_alignment_score(
  tasks: list[str],
  goals: list[Goal],
  embedding_fn=None,
) -> float:
  """Keyword + embedding overlap between tasks and goals."""
  if not tasks or not goals:
    return 0.0
  tasks_text = " ".join(tasks)
  goals_text = " ".join(f"{g.title} {g.description or ''} {g.reason or ''}" for g in goals)
  if embedding_fn:
    similarity = embedding_fn(tasks_text, goals_text)
  else:
    similarity = _text_similarity(tasks_text, goals_text)
  return min(max(similarity * 100, 0.0), 100.0)


def consistency_score(logs_30d: list[DailyLog]) -> float:
  """Streak + execution rate over 30 days."""
  if not logs_30d:
    return 0.0

  sorted_logs = sorted(logs_30d, key=lambda x: x.date, reverse=True)
  streak_days = 0
  expected = sorted_logs[0].date
  for log in sorted_logs:
    if log.date == expected and (log.morning_completed or log.evening_completed):
      streak_days += 1
      expected -= timedelta(days=1)
    else:
      break

  completed_days = sum(1 for log in logs_30d if log.morning_completed or log.evening_completed)
  total_days = min(len(logs_30d), 30)
  execution_rate = completed_days / total_days if total_days > 0 else 0.0

  streak_component = min(streak_days / 30, 1.0) * 40
  execution_component = execution_rate * 60
  return min(streak_component + execution_component, 100.0)


def health_score(
  sleep_hours: Optional[float],
  sleep_quality: Optional[int],
  workout: Optional[bool],
  energy: Optional[int],
) -> float:
  """Health score from sleep, workout, and energy."""
  sleep = normalize(sleep_hours, 4, 9) * 40
  workout_pts = 30 if workout else 0
  energy_pts = normalize(energy, 1, 5) * 30
  return min(sleep + workout_pts + energy_pts, 100.0)


def learning_score(journal_text: str, tasks: list[str]) -> float:
  """Keyword detection in journal and tasks."""
  combined = f"{journal_text} {' '.join(tasks)}".lower()
  if not combined.strip():
    return 0.0
  matches = sum(1 for kw in LEARNING_KEYWORDS if kw in combined)
  return min(matches * 20, 100.0)


def productivity_score(
  deep_work_hours: Optional[float],
  tasks_completed: Optional[float],
  focus: Optional[int],
) -> float:
  """Productivity from deep work, task completion, and focus."""
  deep_work = normalize(deep_work_hours, 0, 6) * 50
  tasks_done = min(tasks_completed or 0, 1.0) * 30
  focus_pts = normalize(focus, 1, 5) * 20
  return min(deep_work + tasks_done + focus_pts, 100.0)


def linear_regression_slope(values: list[float]) -> float:
  """Simple linear regression slope."""
  n = len(values)
  if n < 2:
    return 0.0
  x_mean = (n - 1) / 2
  y_mean = sum(values) / n
  numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
  denominator = sum((i - x_mean) ** 2 for i in range(n))
  if denominator == 0:
    return 0.0
  return numerator / denominator


def momentum_score(scores_7d: list[float]) -> float:
  """Linear regression slope on 7-day overall scores."""
  if not scores_7d:
    return 50.0
  slope = linear_regression_slope(scores_7d)
  return min(max(normalize(slope, -10, 10) * 100, 0.0), 100.0)


def gap_score(goals: list[Goal], logs: list[DailyLog], today: Optional[date] = None) -> float:
  """Pace vs required pace per goal, aggregated."""
  if not goals:
    return 100.0
  today = today or date.today()
  gaps: list[float] = []
  for goal in goals:
    if goal.status != "active":
      continue
    if not goal.deadline:
      gaps.append(100.0 - goal.progress * 100)
      continue
    total_days = (goal.deadline - goal.created_at.date() if goal.created_at else today).days
    if total_days <= 0:
      gaps.append(100.0 if goal.progress < 1.0 else 0.0)
      continue
    elapsed = (today - (goal.created_at.date() if goal.created_at else today)).days
    required_pace = min(elapsed / total_days, 1.0)
    actual_pace = goal.progress
    gap = max(0.0, (required_pace - actual_pace) * 100)
    gaps.append(min(gap, 100.0))
  if not gaps:
    return 100.0
  avg_gap = sum(gaps) / len(gaps)
  return min(max(100.0 - avg_gap, 0.0), 100.0)


def overall_growth_score(
  goal_alignment: float,
  consistency: float,
  health: float,
  productivity: float,
  learning: float,
  momentum: float,
) -> float:
  """Weighted combination of all scores."""
  overall = (
    goal_alignment * 0.30
    + consistency * 0.25
    + health * 0.15
    + productivity * 0.15
    + learning * 0.10
    + momentum * 0.05
  )
  return min(max(overall, 0.0), 100.0)


def calculate_daily_scores(
  log: DailyLog,
  goals: list[Goal],
  logs_30d: list[DailyLog],
  scores_7d: list[float],
) -> Score:
  """Calculate all scores for a single day."""
  tasks: list[str] = []
  if log.top_priority:
    tasks.append(log.top_priority)
  if log.supporting_task_1:
    tasks.append(log.supporting_task_1)
  if log.supporting_task_2:
    tasks.append(log.supporting_task_2)
  if log.tasks_completed:
    tasks.append(log.tasks_completed)

  alignment = goal_alignment_score(tasks, goals)
  consistency = consistency_score(logs_30d)
  health = health_score(
    log.sleep_hours, log.sleep_quality, log.workout_completed, log.energy_level
  )
  learning = learning_score(log.journal_entry or "", tasks)
  productivity = productivity_score(
    log.deep_work_hours, log.task_completion_rate, log.expected_focus
  )
  momentum = momentum_score(scores_7d)
  gap = gap_score(goals, logs_30d, log.date)
  overall = overall_growth_score(alignment, consistency, health, productivity, learning, momentum)

  from database.repositories.score_repository import ScoreRepository
  from models.score import ScoreCreate

  score_data = ScoreCreate(
    date=log.date,
    scope="daily",
    goal_alignment_score=alignment,
    consistency_score=consistency,
    health_score=health,
    learning_score=learning,
    productivity_score=productivity,
    momentum_score=momentum,
    overall_growth_score=overall,
    gap_score=gap,
  )
  return ScoreRepository().create(score_data)
