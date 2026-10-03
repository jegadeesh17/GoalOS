"""Deterministic score calculations — no AI."""

import math
from datetime import date, timedelta
from typing import Callable, NamedTuple, Optional

from models.daily_log import DailyLog
from models.goal import Goal
from models.score import Score
from services.journal_helpers import planned_task_list, planned_task_rate
from services.journal_import_service import awake_times
from services.task_link_service import Resolution, completed_texts

# Goal alignment and consistency look at the 14 days ending on the scored day: a day has only about four
# tasks, so a single day is too small a sample.
WINDOW_DAYS = 14
MIN_REVIEWED_TASKS = 5  # fewer reviewed completed tasks than this and alignment is unknown
MIN_LOGGED_DAYS = 7  # fewer logged days than this and consistency is unknown
MIN_WAKE_TIMES = 5  # fewer readable wake times than this and regularity is unknown
SOLID_DAY_SHARE = 0.5  # a day is "solid" when at least half of its tasks are ticked
RHYTHM_WEIGHT = 0.7
WAKE_SD_ZERO_SCORE_HOURS = 2.0  # a wake-time spread of this many hours or more scores 0 regularity
MIN_MOMENTUM_SCORES = 5  # fewer known overall scores in the previous week than this and momentum is unknown


def normalize(value: Optional[float], min_val: float, max_val: float) -> float:
  """Clamp and normalize value to 0-1 range."""
  if value is None:
    return 0.0
  if max_val == min_val:
    return 0.0
  clamped = max(min_val, min(max_val, value))
  return (clamped - min_val) / (max_val - min_val)


class Alignment(NamedTuple):
  """Goal alignment over a window: the score (None when unknown) and how much of the work it is based on."""

  score: Optional[float]
  reviewed: int  # completed tasks whose goal is known (a goal, or reviewed as serving none)
  completed: int  # all completed tasks in the window

  @property
  def coverage(self) -> Optional[float]:
    return self.reviewed / self.completed if self.completed else None


def window_logs(logs: list[DailyLog], day: date, days: int = WINDOW_DAYS) -> list[DailyLog]:
  """Logs in the `days` calendar days ending on `day`."""
  start = day - timedelta(days=days - 1)
  return [log for log in logs if start <= log.date <= day]


def goal_alignment_score(logs: list[DailyLog], resolve: Callable[[str], Resolution]) -> Alignment:
  """Share of completed, reviewed tasks that serve a goal, pooled over the logs given.

  A task whose goal is unknown (unreviewed) is left out of the score, never counted as misaligned. A task
  reviewed as serving no goal stays in the denominator, so a stretch of chores reads as low alignment.
  """
  completed = reviewed = aligned = 0
  for log in logs:
    for text in completed_texts(log):
      completed += 1
      resolution = resolve(text)
      if resolution.kind == "unreviewed":
        continue
      reviewed += 1
      aligned += 1 if resolution.kind == "goal" else 0
  score = aligned / reviewed * 100 if reviewed >= MIN_REVIEWED_TASKS else None
  return Alignment(score, reviewed, completed)


def _is_solid_day(log: DailyLog) -> bool:
  tasks = planned_task_list(log)
  return bool(tasks) and sum(1 for t in tasks if t.get("completed")) / len(tasks) >= SOLID_DAY_SHARE


def wake_regularity(logs: list[DailyLog]) -> Optional[float]:
  """0-100: 100 when the wake time never moves, 0 at a 2 h spread (population sd). None with < 5 wake times."""
  wakes = [times[0] for times in (awake_times(log.awake_range) for log in logs) if times is not None]
  if len(wakes) < MIN_WAKE_TIMES:
    return None
  mean = sum(wakes) / len(wakes)
  sd = math.sqrt(sum((w - mean) ** 2 for w in wakes) / len(wakes))
  return max(0.0, 1 - sd / WAKE_SD_ZERO_SCORE_HOURS) * 100


def consistency_score(logs: list[DailyLog]) -> Optional[float]:
  """Execution rhythm (share of logged days that were solid) blended with wake-time regularity.

  Ignores the morning/evening flags and the mere existence of a row: the importer marks every imported
  day complete, so neither says anything about how the day went. None with fewer than 7 logged days.
  """
  if len(logs) < MIN_LOGGED_DAYS:
    return None
  rhythm = sum(1 for log in logs if _is_solid_day(log)) / len(logs) * 100
  regularity = wake_regularity(logs)
  if regularity is None:
    return rhythm
  return RHYTHM_WEIGHT * rhythm + (1 - RHYTHM_WEIGHT) * regularity


def _share_of_known(parts: list[tuple[Optional[float], float]]) -> Optional[float]:
  """0-100 score over only the (fraction 0-1 or None, weight) parts that have data.

  A part with no data is left out of both the earned and the available points, never
  counted as zero. None when nothing is known.
  """
  known = [(fraction, weight) for fraction, weight in parts if fraction is not None]
  if not known:
    return None
  available = sum(weight for _, weight in known)
  earned = sum(fraction * weight for fraction, weight in known)
  return min(earned / available * 100, 100.0)


def health_score(
  sleep_hours: Optional[float],
  sleep_quality: Optional[int],
  workout: Optional[bool],
  energy: Optional[int],
) -> Optional[float]:
  """Health score from sleep, workout, and energy; only the ones recorded count."""
  return _share_of_known([
    (None if sleep_hours is None else normalize(sleep_hours, 4, 9), 40),
    (None if workout is None else float(workout), 30),
    (None if energy is None else normalize(energy, 1, 5), 30),
  ])


def productivity_score(
  deep_work_hours: Optional[float],
  tasks_completed: Optional[float],
  focus: Optional[int],
) -> Optional[float]:
  """Productivity from deep work, task completion (a 0-1 fraction), and focus; only recorded ones count."""
  return _share_of_known([
    (None if deep_work_hours is None else normalize(deep_work_hours, 0, 6), 50),
    (None if tasks_completed is None else min(tasks_completed, 1.0), 30),
    (None if focus is None else normalize(focus, 1, 5), 20),
  ])


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


def momentum_score(scores_7d: list[float]) -> Optional[float]:
  """Linear regression slope on the previous week's overall scores; None with fewer than 5 of them."""
  if len(scores_7d) < MIN_MOMENTUM_SCORES:
    return None
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
    start = goal.created_at.date() if goal.created_at else today
    total_days = (goal.deadline - start).days
    if total_days <= 0:
      gaps.append(100.0 if goal.progress < 1.0 else 0.0)
      continue
    elapsed = (today - start).days
    required_pace = min(elapsed / total_days, 1.0)
    actual_pace = goal.progress
    gap = max(0.0, (required_pace - actual_pace) * 100)
    gaps.append(min(gap, 100.0))
  if not gaps:
    return 100.0
  avg_gap = sum(gaps) / len(gaps)
  return min(max(100.0 - avg_gap, 0.0), 100.0)


def overall_growth_score(
  goal_alignment: Optional[float],
  consistency: Optional[float],
  health: Optional[float],
  productivity: Optional[float],
  momentum: Optional[float],
) -> Optional[float]:
  """Weighted combination of the scores that are known; unknown ones are left out and weights renormalised."""
  weighted = [
    (goal_alignment, 0.30),
    (consistency, 0.25),
    (health, 0.15),
    (productivity, 0.15),
    (momentum, 0.05),
  ]
  known = [(score, weight) for score, weight in weighted if score is not None]
  if not known:
    return None
  overall = sum(score * weight for score, weight in known) / sum(weight for _, weight in known)
  return min(max(overall, 0.0), 100.0)


def recent_overall_scores(before: date, n: int = 7) -> list[float]:
  """Known overall scores from the n days before `before`, oldest first (what momentum_score expects)."""
  from database.repositories.score_repository import ScoreRepository

  scores = ScoreRepository().get_range(before - timedelta(days=n), before - timedelta(days=1))
  return [s.overall_growth_score for s in scores if s.overall_growth_score is not None]


def recompute_all_scores(since: Optional[date] = None) -> int:
  """Recalculate and store daily scores for every log (from `since` on), oldest first because momentum
  reads the days before. Needed after anything the scores depend on changes besides the day itself: task
  links, goal cues, or an edit to an earlier day inside someone's 14-day window."""
  from database.repositories.goal_repository import GoalRepository
  from database.repositories.log_repository import LogRepository
  from services.task_link_service import TaskLinkService

  logs = sorted(LogRepository().get_all(), key=lambda log: log.date)
  goals = GoalRepository().get_active()
  resolve = TaskLinkService().resolver(goals)
  count = 0
  for log in logs:
    if since is not None and log.date < since:
      continue
    calculate_daily_scores(
      log, goals, [l for l in logs if log.date - timedelta(days=30) <= l.date <= log.date],
      recent_overall_scores(log.date), resolve,
    )
    count += 1
  return count


def calculate_daily_scores(
  log: DailyLog,
  goals: list[Goal],
  logs_30d: list[DailyLog],
  scores_7d: list[float],
  resolve: Optional[Callable[[str], Resolution]] = None,
) -> Score:
  """Calculate all scores for a single day. `resolve` maps a task's text to its goal (built from the saved
  links and goal cues when omitted; pass one when scoring many days in a row)."""
  if resolve is None:
    from services.task_link_service import TaskLinkService

    resolve = TaskLinkService().resolver(goals)
  window = window_logs(logs_30d, log.date)
  alignment = goal_alignment_score(window, resolve).score
  consistency = consistency_score(window)
  health = health_score(
    log.sleep_hours, log.sleep_quality, log.workout_completed, log.energy_level
  )
  # Derive the rate from the task list: the stored task_completion_rate is a percent from the import
  # script but a 0-1 fraction when the Journal editor autosaves, so it is only a fallback.
  rate = planned_task_rate(log)
  if rate is None:
    rate = log.task_completion_rate
  task_fraction = None if rate is None else rate / 100
  productivity = productivity_score(log.deep_work_hours, task_fraction, log.expected_focus)
  momentum = momentum_score(scores_7d)
  gap = gap_score(goals, logs_30d, log.date)
  overall = overall_growth_score(alignment, consistency, health, productivity, momentum)

  from database.repositories.score_repository import ScoreRepository
  from models.score import ScoreCreate

  score_data = ScoreCreate(
    date=log.date,
    scope="daily",
    goal_alignment_score=alignment,
    consistency_score=consistency,
    health_score=health,
    productivity_score=productivity,
    momentum_score=momentum,
    overall_growth_score=overall,
    gap_score=gap,
  )
  return ScoreRepository().create(score_data)
