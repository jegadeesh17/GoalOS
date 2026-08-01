"""Goal repository."""

from typing import Optional

from database.connection import get_db
from database.repositories._helpers import build_update, row_to_dict
from models.goal import Goal, GoalCreate, GoalUpdate


class GoalRepository:
  """CRUD operations for goals."""

  def create(self, goal: GoalCreate) -> Goal:
    data = goal.model_dump()
    with get_db() as conn:
      columns = ", ".join(data.keys())
      placeholders = ", ".join("?" * len(data))
      cursor = conn.execute(
        f"INSERT INTO goals ({columns}) VALUES ({placeholders})",
        list(data.values()),
      )
      goal_id = cursor.lastrowid
      row = conn.execute("SELECT * FROM goals WHERE id = ?", (goal_id,)).fetchone()
    return Goal(**row_to_dict(row))

  def get_by_id(self, goal_id: int) -> Optional[Goal]:
    with get_db() as conn:
      row = conn.execute("SELECT * FROM goals WHERE id = ?", (goal_id,)).fetchone()
    return Goal(**row_to_dict(row)) if row else None

  def get_all(
    self,
    status: Optional[str] = None,
    category: Optional[str] = None,
    horizon: Optional[str] = None,
  ) -> list[Goal]:
    query = "SELECT * FROM goals WHERE 1=1"
    params: list = []
    if status:
      query += " AND status = ?"
      params.append(status)
    if category:
      query += " AND category = ?"
      params.append(category)
    if horizon:
      query += " AND horizon = ?"
      params.append(horizon)
    query += " ORDER BY priority ASC, created_at DESC"
    with get_db() as conn:
      rows = conn.execute(query, params).fetchall()
    return [Goal(**row_to_dict(r)) for r in rows]

  def get_active(self) -> list[Goal]:
    return self.get_all(status="active")

  def get_by_horizons(self) -> dict[str, list[Goal]]:
    """Return active goals grouped into short-term (1-month), mid-term (1-year), long-term (5-year)."""
    active = self.get_active()
    categorized: dict[str, list[Goal]] = {
      "1-month": [],
      "1-year": [],
      "5-year": [],
      "other": [],
    }
    for goal in active:
      h = (goal.horizon or "").lower().strip()
      if h in ("1-month", "1_month", "short", "weekly", "monthly"):
        categorized["1-month"].append(goal)
      elif h in ("1-year", "1_year", "medium", "yearly", "annual"):
        categorized["1-year"].append(goal)
      elif h in ("5-year", "5_year", "long", "vision", "5-years"):
        categorized["5-year"].append(goal)
      else:
        categorized["other"].append(goal)
    return categorized

  def get_goals_for_month(self, month_date) -> dict[str, list[Goal]]:
    """Return active goals specifically aligned with the given month's year and month."""
    categorized = self.get_by_horizons()
    month_year = (month_date.year, month_date.month)

    matching_1m = []
    seen_titles = set()
    for g in categorized.get("1-month", []):
      if g.deadline:
        if (g.deadline.year, g.deadline.month) == month_year:
          title_key = g.title.strip().lower()
          if title_key not in seen_titles:
            seen_titles.add(title_key)
            matching_1m.append(g)
      else:
        title_key = g.title.strip().lower()
        if title_key not in seen_titles:
          seen_titles.add(title_key)
          matching_1m.append(g)

    if not matching_1m and categorized.get("1-month"):
      for g in categorized["1-month"]:
        title_key = g.title.strip().lower()
        if title_key not in seen_titles:
          seen_titles.add(title_key)
          matching_1m.append(g)

    return {
      "1-month": matching_1m,
      "1-year": categorized.get("1-year", []),
      "5-year": categorized.get("5-year", []),
    }

  def update(self, goal_id: int, goal: GoalUpdate) -> Optional[Goal]:
    data = goal.model_dump(exclude_unset=True)
    if not data:
      return self.get_by_id(goal_id)
    set_clause, values = build_update(data)
    values.append(goal_id)
    with get_db() as conn:
      conn.execute(
        f"UPDATE goals SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        values,
      )
    return self.get_by_id(goal_id)

  def delete(self, goal_id: int) -> bool:
    with get_db() as conn:
      cursor = conn.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
    return cursor.rowcount > 0

  def count(self) -> int:
    with get_db() as conn:
      row = conn.execute("SELECT COUNT(*) FROM goals").fetchone()
    return row[0]
