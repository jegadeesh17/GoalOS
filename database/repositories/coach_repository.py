"""Coach response repository."""

from datetime import date
from typing import Optional

from database.connection import get_db
from database.repositories._helpers import row_to_dict
from models.coach_response import CoachResponse, CoachResponseCreate


class CoachRepository:
  """CRUD operations for coach responses."""

  def create(self, response: CoachResponseCreate) -> CoachResponse:
    data = response.model_dump(mode="json")
    with get_db() as conn:
      columns = ", ".join(data.keys())
      placeholders = ", ".join("?" * len(data))
      cursor = conn.execute(
        f"INSERT INTO coach_responses ({columns}) VALUES ({placeholders})",
        list(data.values()),
      )
      response_id = cursor.lastrowid
      row = conn.execute(
        "SELECT * FROM coach_responses WHERE id = ?", (response_id,)
      ).fetchone()
    return CoachResponse(**row_to_dict(row))

  def get_by_id(self, response_id: int) -> Optional[CoachResponse]:
    with get_db() as conn:
      row = conn.execute(
        "SELECT * FROM coach_responses WHERE id = ?", (response_id,)
      ).fetchone()
    return CoachResponse(**row_to_dict(row)) if row else None

  def get_recent(self, last_n: int = 3) -> list[CoachResponse]:
    with get_db() as conn:
      rows = conn.execute(
        "SELECT * FROM coach_responses ORDER BY created_at DESC LIMIT ?",
        (last_n,),
      ).fetchall()
    return [CoachResponse(**row_to_dict(r)) for r in rows]

  def get_by_date(self, response_date: date) -> list[CoachResponse]:
    with get_db() as conn:
      rows = conn.execute(
        "SELECT * FROM coach_responses WHERE date = ? ORDER BY created_at DESC",
        (response_date.isoformat(),),
      ).fetchall()
    return [CoachResponse(**row_to_dict(r)) for r in rows]

  def get_by_session_type(self, session_type: str, last_n: int = 10) -> list[CoachResponse]:
    with get_db() as conn:
      rows = conn.execute(
        "SELECT * FROM coach_responses WHERE session_type = ? ORDER BY created_at DESC LIMIT ?",
        (session_type, last_n),
      ).fetchall()
    return [CoachResponse(**row_to_dict(r)) for r in rows]

  def delete(self, response_id: int) -> bool:
    with get_db() as conn:
      cursor = conn.execute("DELETE FROM coach_responses WHERE id = ?", (response_id,))
    return cursor.rowcount > 0

  def count(self) -> int:
    with get_db() as conn:
      row = conn.execute("SELECT COUNT(*) FROM coach_responses").fetchone()
    return row[0]
