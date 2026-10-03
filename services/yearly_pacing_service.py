"""Pace of yearly-and-beyond goals against their numeric targets, from the user's monthly check-ins.

Only goals the user gave a numeric target (and checks in on) can be measured. Everything else is
reported as it is: "qualitative", "no_check_ins", "baseline_only", "no_deadline". Nothing is inferred
from journal text and no progress number is ever invented.

By default the expected value rises in a straight line from the start to the target at the deadline.
A goal that grows back-loaded (net worth, say) can carry the user's own dated values ("pace points");
the expected value then follows their path, joined point to point in straight segments. The curve is
never assumed: it is only what the user wrote.
"""

from __future__ import annotations

import calendar
from datetime import date
from typing import Any, Optional

from database.repositories.goal_repository import GoalRepository
from database.repositories.monthly_repository import MonthlyRepository
from models.goal import Goal
from models.monthly import GoalMeasurement, GoalPacePoint

BAND = 0.10  # within 10% of the start-to-target span of the expected value counts as on pace
HORIZONS = ("1-year", "5-year", "10-year")


def _month_end(month: str) -> date:
  year, mon = (int(part) for part in month.split("-"))
  return date(year, mon, calendar.monthrange(year, mon)[1])


def _round(value: float) -> float:
  return round(value, 2)


def _projection(points: list[tuple[date, float]], deadline: date, target: float, sign: int) -> Optional[dict[str, Any]]:
  """Least-squares line through the check-ins, read at the deadline. Needs at least three."""
  if len(points) < 3:
    return None
  origin = points[0][0]
  xs = [(d - origin).days for d, _ in points]
  ys = [v for _, v in points]
  mean_x, mean_y = sum(xs) / len(xs), sum(ys) / len(ys)
  sxx = sum((x - mean_x) ** 2 for x in xs)
  if sxx == 0:
    return None
  slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True)) / sxx
  projected = mean_y + slope * ((deadline - origin).days - mean_x)
  return {"value_at_deadline": _round(projected), "on_track": (projected - target) * sign >= 0}


def _expected_on_path(anchors: list[tuple[date, float]], as_of: date) -> tuple[float, float]:
  """(expected value on `as_of`, size of the segment it falls in) along straight segments between anchors.

  On an anchor's own date the segment that ends there is used. The band that separates "on pace" from
  ahead or behind is a share of that segment, so an early stretch of a back-loaded path is judged on
  its own small scale and not on the size of the final target.
  """
  for (start, start_value), (end, end_value) in zip(anchors, anchors[1:], strict=False):
    if as_of <= end:
      days = (end - start).days
      share = 1.0 if days <= 0 else min(1.0, max(0.0, (as_of - start).days / days))
      return start_value + (end_value - start_value) * share, abs(end_value - start_value)
  last, before = anchors[-1][1], anchors[-2][1]
  return last, abs(last - before)


class YearlyPacingService:
  """Evaluates measurable goals; reads goals and check-ins, writes nothing."""

  def __init__(self, goal_repo: Optional[GoalRepository] = None, monthly_repo: Optional[MonthlyRepository] = None):
    self.goal_repo = goal_repo or GoalRepository()
    self.monthly_repo = monthly_repo or MonthlyRepository()

  def evaluate_all(self, horizon: Optional[str] = None, today: Optional[date] = None) -> list[dict[str, Any]]:
    today = today or date.today()
    grouped = self.goal_repo.get_by_horizons()
    wanted = (horizon,) if horizon else HORIZONS
    results = []
    for name in wanted:
      for goal in grouped.get(name, []):
        results.append(
          self.evaluate(
            goal, self.monthly_repo.get_measurements(goal.id), today, self.monthly_repo.get_pace_points(goal.id)
          )
        )
    return results

  def evaluate(
    self,
    goal: Goal,
    measurements: list[GoalMeasurement],
    today: date,
    pace_points: Optional[list[GoalPacePoint]] = None,
  ) -> dict[str, Any]:
    base: dict[str, Any] = {
      "goal_id": goal.id,
      "title": goal.title.strip(),
      "horizon": goal.horizon,
      "deadline": goal.deadline.isoformat() if goal.deadline else None,
      "metric_name": goal.metric_name,
      "metric_unit": goal.metric_unit,
      "start_value": goal.start_value,
      "target_value": goal.target_value,
      "check_ins": len(measurements),
      "status": None,
      "path": "linear",
      "baseline": None,
      "latest": None,
      "expected_now": None,
      "gap": None,
      "pct_of_target": None,
      "projection": None,
    }
    if goal.target_value is None:
      return {**base, "status": "qualitative"}
    if not measurements:
      return {**base, "status": "no_check_ins"}
    measurements = sorted(measurements, key=lambda m: m.month)
    latest = measurements[-1]
    base["latest"] = {"month": latest.month, "value": latest.value}
    if goal.deadline is None:
      return {**base, "status": "no_deadline"}

    if goal.start_value is not None:
      baseline_value = goal.start_value
      baseline_date = goal.created_at.date() if goal.created_at else _month_end(measurements[0].month)
      baseline = {"value": baseline_value, "source": "start_value", "date": baseline_date.isoformat()}
    else:
      first = measurements[0]
      baseline_value = first.value
      baseline_date = _month_end(first.month)
      baseline = {"value": baseline_value, "source": "first_check_in", "date": baseline_date.isoformat()}
      if len(measurements) == 1:
        return {**base, "status": "baseline_only", "baseline": baseline}
    base["baseline"] = baseline

    span = goal.target_value - baseline_value
    if span == 0:
      return {**base, "status": "on_pace", "pct_of_target": 100.0}
    sign = 1 if span > 0 else -1
    as_of = min(today, _month_end(latest.month))
    own = sorted(
      (p.due, p.value) for p in pace_points or [] if baseline_date < p.due < goal.deadline
    )
    anchors = [(baseline_date, baseline_value), *own, (goal.deadline, goal.target_value)]
    expected, segment = _expected_on_path(anchors, as_of)
    signed_gap = (latest.value - expected) * sign
    if signed_gap > BAND * segment:
      status = "ahead"
    elif signed_gap < -BAND * segment:
      status = "behind"
    else:
      status = "on_pace"
    points = [(_month_end(m.month), m.value) for m in measurements]
    # A straight-line trend to the deadline would contradict a path the user wrote as back-loaded.
    projection = None if own else _projection(points, goal.deadline, goal.target_value, sign)
    return {
      **base,
      "status": status,
      "path": "custom" if own else "linear",
      "expected_now": _round(expected),
      "gap": _round(latest.value - expected),
      "pct_of_target": round((latest.value - baseline_value) / span * 100, 1),
      "projection": projection,
    }
