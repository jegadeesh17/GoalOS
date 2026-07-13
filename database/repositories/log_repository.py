"""Daily log repository."""

from datetime import date
from typing import Optional

from database.connection import get_db
from database.repositories._helpers import build_update, row_to_dict
from models.daily_log import DailyLog, DailyLogCreate, DailyLogUpdate


class LogRepository:
  """CRUD operations for daily logs."""

  def create(self, log: DailyLogCreate) -> DailyLog:
    data = log.model_dump(mode="json")
    data["morning_completed"] = int(data.get("morning_completed", False))
    data["evening_completed"] = int(data.get("evening_completed", False))
    data["imported"] = int(data.get("imported", False))
    if data.get("workout_completed") is not None:
      data["workout_completed"] = int(data["workout_completed"])
    with get_db() as conn:
      columns = ", ".join(data.keys())
      placeholders = ", ".join("?" * len(data))
      cursor = conn.execute(
        f"INSERT INTO daily_logs ({columns}) VALUES ({placeholders})",
        list(data.values()),
      )
      log_id = cursor.lastrowid
      row = conn.execute("SELECT * FROM daily_logs WHERE id = ?", (log_id,)).fetchone()
    return self._to_model(row)

  def get_by_id(self, log_id: int) -> Optional[DailyLog]:
    with get_db() as conn:
      row = conn.execute("SELECT * FROM daily_logs WHERE id = ?", (log_id,)).fetchone()
    return self._to_model(row) if row else None

  def get_by_date(self, log_date: date) -> Optional[DailyLog]:
    with get_db() as conn:
      row = conn.execute(
        "SELECT * FROM daily_logs WHERE date = ?", (log_date.isoformat(),)
      ).fetchone()
    return self._to_model(row) if row else None

  def get_recent(self, last_n: int = 7) -> list[DailyLog]:
    with get_db() as conn:
      rows = conn.execute(
        "SELECT * FROM daily_logs ORDER BY date DESC LIMIT ?", (last_n,)
      ).fetchall()
    return [self._to_model(r) for r in rows]

  def get_range(self, start: date, end: date) -> list[DailyLog]:
    with get_db() as conn:
      rows = conn.execute(
        "SELECT * FROM daily_logs WHERE date >= ? AND date <= ? ORDER BY date ASC",
        (start.isoformat(), end.isoformat()),
      ).fetchall()
    return [self._to_model(r) for r in rows]

  def get_all(self) -> list[DailyLog]:
    with get_db() as conn:
      rows = conn.execute("SELECT * FROM daily_logs ORDER BY date DESC").fetchall()
    return [self._to_model(r) for r in rows]

  def update(self, log_id: int, log: DailyLogUpdate) -> Optional[DailyLog]:
    data = log.model_dump(exclude_unset=True)
    if "morning_completed" in data:
      data["morning_completed"] = int(data["morning_completed"])
    if "evening_completed" in data:
      data["evening_completed"] = int(data["evening_completed"])
    if "imported" in data:
      data["imported"] = int(data["imported"])
    if "workout_completed" in data and data["workout_completed"] is not None:
      data["workout_completed"] = int(data["workout_completed"])
    if not data:
      return self.get_by_id(log_id)
    set_clause, values = build_update(data)
    values.append(log_id)
    with get_db() as conn:
      conn.execute(
        f"UPDATE daily_logs SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        values,
      )
    return self.get_by_id(log_id)

  def upsert_by_date(self, log: DailyLogCreate) -> DailyLog:
    """Legacy full-form upsert that does not erase existing optional fields."""
    existing = self.get_by_date(log.date)
    if existing:
      data = log.model_dump(mode="json", exclude_none=True)
      # ``DailyLogCreate`` has false defaults. Treat them as omitted for a merge so
      # saving a morning form cannot reset an already-completed evening.
      for field in ("morning_completed", "evening_completed", "imported"):
        if data.get(field) is False:
          data.pop(field)
      data.pop("date", None)
      return self.update(existing.id, DailyLogUpdate(**data))  # type: ignore[arg-type]
    return self.create(log)

  def upsert_fields(self, log_date: date, changes: DailyLogUpdate) -> DailyLog:
    """Create a dated log or apply only explicitly supplied fields to it."""
    existing = self.get_by_date(log_date)
    if existing:
      updated = self.update(existing.id, changes)
      assert updated is not None
      return updated
    create_data = changes.model_dump(exclude_unset=True)
    return self.create(DailyLogCreate(date=log_date, **create_data))

  def delete(self, log_id: int) -> bool:
    with get_db() as conn:
      cursor = conn.execute("DELETE FROM daily_logs WHERE id = ?", (log_id,))
    return cursor.rowcount > 0

  def count(self) -> int:
    with get_db() as conn:
      row = conn.execute("SELECT COUNT(*) FROM daily_logs").fetchone()
    return row[0]

  def _to_model(self, row) -> DailyLog:
    data = row_to_dict(row)
    for bool_field in ("morning_completed", "evening_completed", "imported", "workout_completed"):
      if data.get(bool_field) is not None:
        data[bool_field] = bool(data[bool_field])
    return DailyLog(**data)
