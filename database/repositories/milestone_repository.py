"""Persistence operations for goal milestones."""

from typing import Optional

from database.connection import get_db
from database.repositories._helpers import build_update, row_to_dict
from models.milestone import Milestone, MilestoneCreate, MilestoneUpdate


class MilestoneRepository:
  def create(self, milestone: MilestoneCreate) -> Milestone:
    data = milestone.model_dump(mode="json")
    with get_db() as conn:
      goal = conn.execute("SELECT id FROM goals WHERE id = ?", (milestone.goal_id,)).fetchone()
      if not goal:
        raise ValueError("goal_id does not reference an existing goal")
      columns = ", ".join(data)
      placeholders = ", ".join("?" * len(data))
      cursor = conn.execute(f"INSERT INTO milestones ({columns}) VALUES ({placeholders})", list(data.values()))
      row = conn.execute("SELECT * FROM milestones WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return Milestone(**row_to_dict(row))

  def get_by_id(self, milestone_id: int) -> Optional[Milestone]:
    with get_db() as conn:
      row = conn.execute("SELECT * FROM milestones WHERE id = ?", (milestone_id,)).fetchone()
    return Milestone(**row_to_dict(row)) if row else None

  def get_for_goal(self, goal_id: int, include_archived: bool = False) -> list[Milestone]:
    query = "SELECT * FROM milestones WHERE goal_id = ?"
    if not include_archived:
      query += " AND status != 'archived'"
    query += " ORDER BY deadline IS NULL, deadline, created_at"
    with get_db() as conn:
      rows = conn.execute(query, (goal_id,)).fetchall()
    return [Milestone(**row_to_dict(row)) for row in rows]

  def get_active(self) -> list[Milestone]:
    with get_db() as conn:
      rows = conn.execute("SELECT * FROM milestones WHERE status = 'active' ORDER BY deadline IS NULL, deadline").fetchall()
    return [Milestone(**row_to_dict(row)) for row in rows]

  def update(self, milestone_id: int, milestone: MilestoneUpdate) -> Optional[Milestone]:
    set_clause, values = build_update(milestone.model_dump(exclude_unset=True))
    if not set_clause:
      return self.get_by_id(milestone_id)
    values.append(milestone_id)
    with get_db() as conn:
      conn.execute(f"UPDATE milestones SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", values)
    return self.get_by_id(milestone_id)

  def delete(self, milestone_id: int) -> bool:
    with get_db() as conn:
      return conn.execute("DELETE FROM milestones WHERE id = ?", (milestone_id,)).rowcount > 0
