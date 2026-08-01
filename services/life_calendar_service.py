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
