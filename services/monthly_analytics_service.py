"""Stored month-by-month analytics: facts derived from the daily logs, recomputable at any time.

A snapshot is a cache, not a source of truth: `recompute_month` rebuilds it from `daily_logs` and
`scores`, so late imports and data fixes just trigger a recompute. Unknown stays unknown (None):
means skip missing values and report how many days they used.
"""

from __future__ import annotations

import calendar
import json
import statistics
from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import Any, Literal, Optional

from database.repositories.goal_repository import GoalRepository
from database.repositories.log_repository import LogRepository
from database.repositories.monthly_repository import MonthlyRepository
from database.repositories.score_repository import ScoreRepository
from models.daily_log import DailyLog
from models.monthly import MonthlyGoalResult, MonthlySnapshot
from services.journal_helpers import planned_task_list, planned_task_rate, task_key
from services.journal_import_service import awake_times
from services.monthly_levers import build_focus, clock_label, compute_levers

SCHEMA_VERSION = 1
MIN_AWAKE_HOURS = 10.0  # a shorter wake-to-bed window is an AM/PM slip, not a bedtime
SOLID_DAY_PERCENT = 50.0  # a "solid" day: at least half of the day's tasks ticked
STUCK_MIN_PLANNED = 3
LEVER_WINDOW_DAYS = 90
SCORE_FIELDS = {
  "overall": "overall_growth_score",
  "health": "health_score",
  "productivity": "productivity_score",
  "momentum": "momentum_score",
  "goal_alignment": "goal_alignment_score",
  "consistency": "consistency_score",
}


def month_bounds(month: str) -> tuple[date, date]:
  year, mon = (int(part) for part in month.split("-"))
  return date(year, mon, 1), date(year, mon, calendar.monthrange(year, mon)[1])


def previous_month(month: str) -> str:
  first, _ = month_bounds(month)
  last_of_previous = first - timedelta(days=1)
  return f"{last_of_previous.year:04d}-{last_of_previous.month:02d}"


def _mean(values: list[float], digits: int = 2) -> Optional[float]:
  return round(statistics.mean(values), digits) if values else None


def _time_stats(hours: list[float]) -> dict[str, Any]:
  return {
    "n": len(hours),
    "avg_hour": _mean(hours),
    "avg_clock": clock_label(statistics.mean(hours)) if hours else None,
    "sd": round(statistics.pstdev(hours), 2) if len(hours) >= 2 else None,
  }


def _filled_plan_hours(log: DailyLog) -> Optional[int]:
  if not log.time_blocks:
    return None
  try:
    blocks = json.loads(log.time_blocks)
  except json.JSONDecodeError:
    return None
  if not isinstance(blocks, list):
    return None
  return sum(1 for b in blocks if isinstance(b, dict) and str(b.get("activity") or "").strip())


def _sleep_unknown_reason(log: DailyLog, by_date: dict[date, DailyLog]) -> str:
  if not log.awake_range:
    return "no_awake_line"
  if awake_times(log.awake_range) is None:
    return "unreadable_awake_line"
  previous = by_date.get(log.date - timedelta(days=1))
  if previous is None:
    return "no_previous_day"
  if awake_times(previous.awake_range) is None:
    return "previous_bedtime_unreadable"
  return "implausible_bedtime"


def compute_month_metrics(
  month: str,
  logs: list[DailyLog],
  scores: list[Any],
  by_date: dict[date, DailyLog],
) -> dict[str, Any]:
  """Facts for one month. `logs` are the month's logs; `by_date` also holds the day before it."""
  start, end = month_bounds(month)
  logs = sorted(logs, key=lambda log: log.date)

  planned = done = solid = zero = 0
  weekly: dict[date, list[int]] = defaultdict(lambda: [0, 0])
  task_counts: dict[str, list[Any]] = {}
  wake: list[float] = []
  bed: list[float] = []
  excluded_bedtimes = 0
  sleep: list[float] = []
  unknown_reasons: Counter[str] = Counter()
  plan_filled: list[float] = []

  for log in logs:
    tasks = planned_task_list(log)
    day_done = sum(1 for t in tasks if t.get("completed"))
    planned += len(tasks)
    done += day_done
    monday = log.date - timedelta(days=log.date.weekday())
    weekly[monday][0] += len(tasks)
    weekly[monday][1] += day_done
    if tasks:
      if day_done / len(tasks) * 100 >= SOLID_DAY_PERCENT:
        solid += 1
      if day_done == 0:
        zero += 1
    for t in tasks:
      entry = task_counts.setdefault(task_key(t["text"]), [t["text"].strip(), 0, 0])
      entry[1] += 1
      entry[2] += 1 if t.get("completed") else 0

    times = awake_times(log.awake_range)
    if times:
      wake.append(times[0])
      if (times[1] - times[0]) % 24 >= MIN_AWAKE_HOURS:
        bed.append(times[1] + 24 if times[1] < 12 else times[1])
      else:
        excluded_bedtimes += 1
    if log.sleep_hours is not None:
      sleep.append(log.sleep_hours)
    else:
      unknown_reasons[_sleep_unknown_reason(log, by_date)] += 1
    filled = _filled_plan_hours(log)
    if filled is not None:
      plan_filled.append(filled)

  stuck = sorted(
    (
      {"task": text, "planned": n, "done": d}
      for text, n, d in task_counts.values()
      if n >= STUCK_MIN_PLANNED and d / n < 0.5
    ),
    key=lambda item: (-item["planned"], item["task"].casefold()),
  )

  score_means: dict[str, Optional[float]] = {}
  for label, field in SCORE_FIELDS.items():
    values = [getattr(s, field) for s in scores if getattr(s, field) is not None]
    score_means[label] = _mean(values, 1)

  bed_stats = _time_stats(bed)
  bed_stats["excluded"] = excluded_bedtimes
  return {
    "days_in_month": (end - start).days + 1,
    "days_logged": len(logs),
    "tasks": {
      "planned": planned,
      "done": done,
      "completion_rate": round(done / planned * 100, 1) if planned else None,
      "per_day": round(planned / len(logs), 2) if logs else None,
      "solid_days": solid,
      "zero_days": zero,
      "weekly": [
        {
          "week_start": monday.isoformat(),
          "planned": counts[0],
          "done": counts[1],
          "rate": round(counts[1] / counts[0] * 100, 1) if counts[0] else None,
        }
        for monday, counts in sorted(weekly.items())
      ],
    },
    "sleep": {
      "nights_known": len(sleep),
      "avg_hours": _mean(sleep),
      "under_6": sum(1 for h in sleep if h < 6),
      "at_least_7": sum(1 for h in sleep if h >= 7),
      "wake": _time_stats(wake),
      "bedtime": bed_stats,
      "unknown_reasons": dict(unknown_reasons),
    },
    "plan": {"avg_hours_filled": _mean(plan_filled), "n": len(plan_filled)},
    "scores": score_means,
    "stuck_tasks": stuck,
  }


def _headline(metrics: dict[str, Any]) -> dict[str, Optional[float]]:
  logged = metrics["days_logged"]
  return {
    "completion_rate": metrics["tasks"]["completion_rate"],
    "tasks_per_day": metrics["tasks"]["per_day"],
    "solid_day_share": round(metrics["tasks"]["solid_days"] / logged * 100, 1) if logged else None,
    "avg_sleep_hours": metrics["sleep"]["avg_hours"],
    "wake_hour": metrics["sleep"]["wake"]["avg_hour"],
    "plan_hours_filled": metrics["plan"]["avg_hours_filled"],
    "score_overall": metrics["scores"]["overall"],
    "score_health": metrics["scores"]["health"],
    "score_productivity": metrics["scores"]["productivity"],
  }


def _deltas(current: dict[str, Any], previous: Optional[dict[str, Any]]) -> dict[str, float]:
  if previous is None:
    return {}
  now, before = _headline(current), _headline(previous)
  return {
    name: round(now[name] - before[name], 2)  # type: ignore[operator]
    for name in now
    if now[name] is not None and before[name] is not None
  }


class MonthlyAnalyticsService:
  """Builds, stores and serves month-by-month snapshots."""

  def __init__(
    self,
    log_repo: Optional[LogRepository] = None,
    score_repo: Optional[ScoreRepository] = None,
    goal_repo: Optional[GoalRepository] = None,
    monthly_repo: Optional[MonthlyRepository] = None,
  ):
    self.log_repo = log_repo or LogRepository()
    self.score_repo = score_repo or ScoreRepository()
    self.goal_repo = goal_repo or GoalRepository()
    self.repo = monthly_repo or MonthlyRepository()

  # ---- reads

  def get_snapshot(self, month: str) -> Optional[MonthlySnapshot]:
    return self.repo.get_snapshot(month)

  def list_snapshots(self) -> list[MonthlySnapshot]:
    return self.repo.list_snapshots()

  def get_goal_results(self, month: str) -> list[MonthlyGoalResult]:
    return self.repo.get_goal_results(month)

  def snapshots_ensuring_built(self) -> list[MonthlySnapshot]:
    """Stored snapshots, building them from the daily logs first if none exist yet (fresh install, demo)."""
    if not self.repo.list_snapshots():
      self.recompute_all()
    return self.repo.list_snapshots()

  def history_digest(self, months: int = 6) -> list[dict[str, Any]]:
    """The last `months` saved months, trimmed to what fits an AI prompt (oldest first)."""
    digest = []
    for snap in self.snapshots_ensuring_built()[-months:]:
      m, insights = snap.metrics, snap.insights or {}
      digest.append({
        "month": snap.month,
        "status": snap.status,
        "data_through": snap.data_through.isoformat() if snap.data_through else None,
        "days_logged": m["days_logged"],
        "days_in_month": m["days_in_month"],
        "tasks": {k: m["tasks"][k] for k in ("planned", "done", "completion_rate", "solid_days", "zero_days")},
        "sleep": {
          "avg_hours": m["sleep"]["avg_hours"],
          "nights_known": m["sleep"]["nights_known"],
          "wake": m["sleep"]["wake"]["avg_clock"],
          "bedtime": m["sleep"]["bedtime"]["avg_clock"],
        },
        "scores": m["scores"],
        "delta_vs_previous": m["delta_vs_previous"],
        "top_levers": [
          {k: f[k] for k in ("lever", "tier", "rho", "n", "contrast")} for f in insights.get("findings", [])[:3]
        ],
        "focus": insights.get("focus", []),
        "stuck_tasks": m["stuck_tasks"][:2],
        "goals": [
          {
            "title": r.goal_title.strip(),
            "horizon": r.horizon,
            "progress": r.progress_at_close,
            "as_of": r.as_of.isoformat(),
          }
          for r in self.repo.get_goal_results(snap.month)
        ],
      })
    return digest

  # ---- recompute

  def recompute_all(self, today: Optional[date] = None, with_insights: bool = True) -> list[MonthlySnapshot]:
    months = sorted({f"{log.date.year:04d}-{log.date.month:02d}" for log in self.log_repo.get_all()})
    snapshots = [self.recompute_month(month, today=today, with_insights=with_insights) for month in months]
    return [s for s in snapshots if s is not None]

  def recompute_month(
    self, month: str, today: Optional[date] = None, with_insights: bool = True
  ) -> Optional[MonthlySnapshot]:
    """Rebuild one month's snapshot. `with_insights=False` skips the (costlier) lever analysis and keeps
    whatever insights are already stored: used on every journal save, where only the facts changed."""
    today = today or date.today()
    start, end = month_bounds(month)
    logs, by_date = self._month_logs(start, end)
    if not logs:
      self.repo.delete_snapshot(month)
      return None

    scores = self.score_repo.get_range(start, end)
    metrics = compute_month_metrics(month, logs, scores, by_date)

    prev_month = previous_month(month)
    prev_start, prev_end = month_bounds(prev_month)
    prev_logs, prev_by_date = self._month_logs(prev_start, prev_end)
    previous = (
      compute_month_metrics(prev_month, prev_logs, self.score_repo.get_range(prev_start, prev_end), prev_by_date)
      if prev_logs
      else None
    )
    metrics["delta_vs_previous"] = _deltas(metrics, previous)

    data_through = max(log.date for log in logs)
    status: Literal["provisional", "final"] = "final" if today > end and data_through == end else "provisional"
    insights = self._compute_insights(month, data_through, metrics) if with_insights else None
    snapshot = self.repo.upsert_snapshot(
      MonthlySnapshot(
        month=month,
        status=status,
        data_through=data_through,
        metrics=metrics,
        insights=insights,
        schema_version=SCHEMA_VERSION,
      )
    )
    self._store_goal_results(month, status, today)
    return snapshot

  # ---- internals

  def _month_logs(self, start: date, end: date) -> tuple[list[DailyLog], dict[date, DailyLog]]:
    around = self.log_repo.get_range(start - timedelta(days=1), end)
    by_date = {log.date: log for log in around}
    return [log for log in around if start <= log.date <= end], by_date

  def _compute_insights(self, month: str, data_through: date, metrics: dict[str, Any]) -> dict[str, Any]:
    """Levers over the trailing 90 days ending at the month's last logged day."""
    window_start = data_through - timedelta(days=LEVER_WINDOW_DAYS - 1)
    around = self.log_repo.get_range(window_start - timedelta(days=1), data_through)
    by_date = {log.date: log for log in around}
    rows = []
    for log in around:
      if log.date < window_start:
        continue
      tasks = planned_task_list(log)
      previous = by_date.get(log.date - timedelta(days=1))
      times = awake_times(log.awake_range)
      previous_times = awake_times(previous.awake_range) if previous else None
      bed_prev = None
      if previous_times and (previous_times[1] - previous_times[0]) % 24 >= MIN_AWAKE_HOURS:
        bed_prev = previous_times[1] + 24 if previous_times[1] < 12 else previous_times[1]
      rows.append({
        "date": log.date,
        "rate": planned_task_rate(log),
        "n_tasks": len(tasks),
        "done": sum(1 for t in tasks if t.get("completed")) if tasks else None,
        "sleep": log.sleep_hours,
        "wake": times[0] if times else None,
        "bed_prev": bed_prev,
        "prev_rate": planned_task_rate(previous),
        "plan_filled": _filled_plan_hours(log),
        "weekend": log.date.weekday() >= 5,
        "tasks": [bool(t.get("completed")) for t in tasks],
      })
    insights = compute_levers(rows, seed=int(month.replace("-", "")))
    insights["focus"] = build_focus(insights["findings"], metrics["stuck_tasks"])
    return insights

  def _store_goal_results(self, month: str, status: str, today: date) -> None:
    """Copy each goal's state for the month, only while the month is current or previous and not yet final.

    Goal progress and titles change over time; recomputing an old month later must never rewrite
    what was true at its close, and must never invent history for months we did not observe.
    """
    this_month = f"{today.year:04d}-{today.month:02d}"
    if month not in (this_month, previous_month(this_month)):
      return
    if status == "final" and self.repo.has_goal_results(month):
      return
    _, end = month_bounds(month)
    results = [
      MonthlyGoalResult(
        month=month,
        goal_id=goal.id,
        goal_title=goal.title,
        horizon=goal.horizon,
        progress_at_close=goal.progress,
        status_at_close=goal.status,
        as_of=today,
      )
      for goal in self.goal_repo.get_all()
      if goal.created_at is None or goal.created_at.date() <= end
    ]
    self.repo.replace_goal_results(month, results)
