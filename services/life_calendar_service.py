"""Life Calendar Service: Calculate weeks lived, remaining, and grid visualization for GoalOS."""

from datetime import date
from typing import Any


class LifeCalendarService:

  def __init__(self, birth_date: date | str = date(2002, 6, 17), target_age: int = 70):
    if isinstance(birth_date, str):
      self.birth_date = date.fromisoformat(birth_date)
    else:
      self.birth_date = birth_date
    self.target_age = target_age

  def get_summary(self, reference_date: date | None = None) -> dict[str, Any]:
    today = reference_date or date.today()
    if today < self.birth_date:
      today = self.birth_date

    days_lived = (today - self.birth_date).days
    weeks_lived = days_lived // 7
    total_weeks = self.target_age * 52
    weeks_remaining = max(0, total_weeks - weeks_lived)
    percentage_lived = round((weeks_lived / total_weeks) * 100, 1) if total_weeks > 0 else 0.0
    age_years = round(days_lived / 365.25, 1)

    target_date = self.birth_date.replace(year=self.birth_date.year + self.target_age)

    return {
      "birth_date": self.birth_date.isoformat(),
      "target_age": self.target_age,
      "today": today.isoformat(),
      "age_years": age_years,
      "total_weeks": total_weeks,
      "weeks_lived": weeks_lived,
      "weeks_remaining": weeks_remaining,
      "percentage_lived": percentage_lived,
      "target_date": target_date.isoformat(),
    }

  def get_grid_data(self, reference_date: date | None = None) -> list[dict[str, Any]]:
    """Returns grid rows per age year (0 to target_age-1) with 52 weeks each."""
    today = reference_date or date.today()
    days_lived = (today - self.birth_date).days
    current_week_index = max(0, days_lived // 7)

    grid = []
    for year in range(self.target_age):
      year_weeks = []
      year_start_week = year * 52
      for week in range(52):
        global_week_index = year_start_week + week
        if global_week_index < current_week_index:
          status = "past"
        elif global_week_index == current_week_index:
          status = "current"
        else:
          status = "future"

        year_weeks.append(
          {
            "year": year,
            "week_of_year": week + 1,
            "global_week": global_week_index + 1,
            "status": status,
          }
        )
      grid.append({"age": year, "weeks": year_weeks})
    return grid

  def get_year_productivity_grid(
    self, year: int | None = None, reference_date: date | None = None
  ) -> dict[str, Any]:
    """Returns all calendar days for the year with productivity statuses, scores, and streak analytics."""
    import calendar
    import json
    from datetime import timedelta

    from database.repositories.log_repository import LogRepository
    from database.repositories.score_repository import ScoreRepository

    today = reference_date or date.today()
    target_year = int(year) if year is not None else today.year

    start_date = date(target_year, 1, 1)
    end_date = date(target_year, 12, 31)
    total_days = (end_date - start_date).days + 1

    # Fetch all logs and daily scores for the year in batch
    log_repo = LogRepository()
    score_repo = ScoreRepository()
    logs = log_repo.get_range(start_date, end_date)
    scores = score_repo.get_range(start_date, end_date, scope="daily")

    logs_by_date = {log.date.isoformat(): log for log in logs}
    scores_by_date = {score.date.isoformat(): score for score in scores}

    days = []
    productive_dates_set = set()

    for day_offset in range(total_days):
      current_day = start_date + timedelta(days=day_offset)
      d_str = current_day.isoformat()

      if current_day > today:
        status = "future"
      elif current_day == today:
        status = "today"
      else:
        status = "past"

      log = logs_by_date.get(d_str)
      score = scores_by_date.get(d_str)

      prod_score = score.productivity_score if score and score.productivity_score is not None else None
      deep_work = log.deep_work_hours if log and log.deep_work_hours is not None else None
      task_rate = log.task_completion_rate if log and log.task_completion_rate is not None else None

      # Parse planned tasks
      tasks_completed_count = 0
      tasks_total_count = 0
      if log and log.planned_tasks:
        try:
          parsed = json.loads(log.planned_tasks)
          if isinstance(parsed, list):
            tasks_total_count = len(parsed)
            tasks_completed_count = sum(1 for t in parsed if isinstance(t, dict) and t.get("completed"))
        except Exception:
          lines = [line.strip() for line in log.planned_tasks.split("\n") if line.strip()]
          tasks_total_count = len(lines)
          tasks_completed_count = sum(1 for line in lines if "(tick)" in line.lower() or "✓" in line)
      elif log and log.tasks_completed:
        lines = [line.strip() for line in log.tasks_completed.split("\n") if line.strip()]
        tasks_completed_count = len(lines)
        tasks_total_count = max(tasks_completed_count, 1)

      # Evaluate productivity (Decision 2 / Rule 1 - Smart Composite)
      is_productive = False
      if status != "future":
        if prod_score is not None and prod_score >= 50.0:
          is_productive = True
        elif deep_work is not None and deep_work >= 1.5:
          is_productive = True
        elif task_rate is not None and task_rate >= 0.5 and tasks_completed_count > 0:
          is_productive = True
        elif log and log.morning_completed and log.evening_completed:
          is_productive = True

      if is_productive:
        productive_dates_set.add(current_day)

      days.append(
        {
          "date": d_str,
          "day_of_year": day_offset + 1,
          "day_of_week": current_day.weekday(),  # 0=Monday, 6=Sunday
          "month": current_day.month,
          "day": current_day.day,
          "status": status,
          "has_log": log is not None,
          "is_productive": is_productive,
          "productivity_score": prod_score,
          "overall_growth_score": score.overall_growth_score if score else None,
          "deep_work_hours": deep_work,
          "task_completion_rate": task_rate,
          "tasks_completed_count": tasks_completed_count,
          "tasks_total_count": tasks_total_count,
          "top_priority": log.top_priority if log else None,
          "one_win": log.one_win if log else None,
          "morning_completed": bool(log.morning_completed) if log else False,
          "evening_completed": bool(log.evening_completed) if log else False,
        }
      )

    # Days elapsed in the year
    if target_year < today.year:
      days_elapsed = total_days
    elif target_year > today.year:
      days_elapsed = 0
    else:
      days_elapsed = min(total_days, (today - start_date).days + 1)

    days_remaining = max(0, total_days - days_elapsed)
    productive_days_count = len(productive_dates_set)
    unproductive_days_count = sum(
      1 for d in days if d["status"] in ("past", "today") and d["has_log"] and not d["is_productive"]
    )
    unlogged_days_count = sum(
      1 for d in days if d["status"] in ("past", "today") and not d["has_log"]
    )
    productivity_rate = (
      round((productive_days_count / days_elapsed) * 100, 1) if days_elapsed > 0 else 0.0
    )

    # Streak calculation
    best_streak = 0
    cur_run = 0
    for day_offset in range(total_days):
      check_date = start_date + timedelta(days=day_offset)
      if check_date in productive_dates_set:
        cur_run += 1
        if cur_run > best_streak:
          best_streak = cur_run
      else:
        cur_run = 0

    current_streak = 0
    if target_year == today.year:
      check_pointer = today
      # If today is not yet productive, check starting from yesterday
      if check_pointer not in productive_dates_set and check_pointer > start_date:
        check_pointer = check_pointer - timedelta(days=1)
      while check_pointer >= start_date and check_pointer in productive_dates_set:
        current_streak += 1
        check_pointer = check_pointer - timedelta(days=1)
    elif target_year < today.year:
      current_streak = 0

    # Monthly breakdown (Jan..Dec)
    months = []
    for m in range(1, 13):
      m_days = [d for d in days if d["month"] == m]
      m_total = len(m_days)
      m_productive = sum(1 for d in m_days if d["is_productive"])
      m_elapsed = sum(1 for d in m_days if d["status"] in ("past", "today"))
      m_rate = round((m_productive / m_elapsed) * 100, 1) if m_elapsed > 0 else 0.0

      months.append(
        {
          "month": m,
          "name": calendar.month_name[m],
          "short_name": calendar.month_abbr[m],
          "total_days": m_total,
          "productive_days": m_productive,
          "days_elapsed": m_elapsed,
          "productivity_rate": m_rate,
        }
      )

    return {
      "year": target_year,
      "total_days": total_days,
      "days_elapsed": days_elapsed,
      "days_remaining": days_remaining,
      "productive_days_count": productive_days_count,
      "unproductive_days_count": unproductive_days_count,
      "unlogged_days_count": unlogged_days_count,
      "productivity_rate": productivity_rate,
      "current_streak": current_streak,
      "best_streak": best_streak,
      "days": days,
      "months": months,
    }
