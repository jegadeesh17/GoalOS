"""Score repository."""

from datetime import date
from typing import Optional

from database.connection import get_db
from database.repositories._helpers import row_to_dict
from models.score import Score, ScoreCreate


class ScoreRepository:
  """CRUD operations for scores."""

  def create(self, score: ScoreCreate) -> Score:
    data = score.model_dump(mode="json")
    with get_db() as conn:
      columns = ", ".join(data.keys())
      placeholders = ", ".join("?" * len(data))
      cursor = conn.execute(
        f"INSERT INTO scores ({columns}) VALUES ({placeholders})",
        list(data.values()),
      )
      score_id = cursor.lastrowid
      row = conn.execute("SELECT * FROM scores WHERE id = ?", (score_id,)).fetchone()
    return Score(**row_to_dict(row))

  def get_by_id(self, score_id: int) -> Optional[Score]:
    with get_db() as conn:
      row = conn.execute("SELECT * FROM scores WHERE id = ?", (score_id,)).fetchone()
    return Score(**row_to_dict(row)) if row else None

  def get_by_date(self, score_date: date, scope: str = "daily") -> Optional[Score]:
    with get_db() as conn:
      row = conn.execute(
        "SELECT * FROM scores WHERE date = ? AND scope = ? ORDER BY calculated_at DESC LIMIT 1",
        (score_date.isoformat(), scope),
      ).fetchone()
    return Score(**row_to_dict(row)) if row else None

  def get_recent(self, last_n: int = 7, scope: str = "daily") -> list[Score]:
    with get_db() as conn:
      rows = conn.execute(
        "SELECT * FROM scores WHERE scope = ? ORDER BY date DESC LIMIT ?",
        (scope, last_n),
      ).fetchall()
    return [Score(**row_to_dict(r)) for r in rows]

  def get_range(self, start: date, end: date, scope: str = "daily") -> list[Score]:
    with get_db() as conn:
      rows = conn.execute(
        "SELECT * FROM scores WHERE date >= ? AND date <= ? AND scope = ? ORDER BY date ASC",
        (start.isoformat(), end.isoformat(), scope),
      ).fetchall()
    return [Score(**row_to_dict(r)) for r in rows]

  def delete(self, score_id: int) -> bool:
    with get_db() as conn:
      cursor = conn.execute("DELETE FROM scores WHERE id = ?", (score_id,))
    return cursor.rowcount > 0

  def count(self) -> int:
    with get_db() as conn:
      row = conn.execute("SELECT COUNT(*) FROM scores").fetchone()
    return row[0]
