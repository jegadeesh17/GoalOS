"""Monthly snapshot, frozen goal-result, and goal-measurement persistence."""

import json
from typing import Optional

from database.connection import get_db
from database.repositories._helpers import row_to_dict
from models.monthly import GoalMeasurement, GoalMeasurementCreate, MonthlyGoalResult, MonthlySnapshot


class MonthlyRepository:
  """CRUD for monthly_snapshots, monthly_goal_results and goal_measurements."""

  # ---- snapshots

  def upsert_snapshot(self, snapshot: MonthlySnapshot) -> MonthlySnapshot:
    with get_db() as conn:
      conn.execute(
        "INSERT INTO monthly_snapshots (month, status, data_through, metrics_json, insights_json, schema_version) "
        "VALUES (?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(month) DO UPDATE SET status=excluded.status, data_through=excluded.data_through, "
        "metrics_json=excluded.metrics_json, "
        "insights_json=COALESCE(excluded.insights_json, monthly_snapshots.insights_json), "
        "schema_version=excluded.schema_version, computed_at=CURRENT_TIMESTAMP",
        (
          snapshot.month,
          snapshot.status,
          snapshot.data_through.isoformat() if snapshot.data_through else None,
          json.dumps(snapshot.metrics),
          json.dumps(snapshot.insights) if snapshot.insights is not None else None,
          snapshot.schema_version,
        ),
      )
    stored = self.get_snapshot(snapshot.month)
    assert stored is not None
    return stored

  def get_snapshot(self, month: str) -> Optional[MonthlySnapshot]:
    with get_db() as conn:
      row = conn.execute("SELECT * FROM monthly_snapshots WHERE month = ?", (month,)).fetchone()
    return self._to_snapshot(row) if row else None

  def list_snapshots(self) -> list[MonthlySnapshot]:
    with get_db() as conn:
      rows = conn.execute("SELECT * FROM monthly_snapshots ORDER BY month ASC").fetchall()
    return [self._to_snapshot(r) for r in rows]

  def delete_snapshot(self, month: str) -> None:
    with get_db() as conn:
      conn.execute("DELETE FROM monthly_snapshots WHERE month = ?", (month,))

  # ---- frozen goal results

  def has_goal_results(self, month: str) -> bool:
    with get_db() as conn:
      return conn.execute("SELECT 1 FROM monthly_goal_results WHERE month = ? LIMIT 1", (month,)).fetchone() is not None

  def get_goal_results(self, month: str) -> list[MonthlyGoalResult]:
    with get_db() as conn:
      rows = conn.execute("SELECT * FROM monthly_goal_results WHERE month = ? ORDER BY goal_id", (month,)).fetchall()
    return [MonthlyGoalResult(**row_to_dict(r)) for r in rows]

  def replace_goal_results(self, month: str, results: list[MonthlyGoalResult]) -> None:
    with get_db() as conn:
      conn.execute("DELETE FROM monthly_goal_results WHERE month = ?", (month,))
      for r in results:
        conn.execute(
          "INSERT INTO monthly_goal_results "
          "(month, goal_id, goal_title, horizon, progress_at_close, status_at_close, as_of) VALUES (?, ?, ?, ?, ?, ?, ?)",
          (r.month, r.goal_id, r.goal_title, r.horizon, r.progress_at_close, r.status_at_close, r.as_of.isoformat()),
        )

  # ---- goal measurements

  def upsert_measurement(self, goal_id: int, data: GoalMeasurementCreate) -> GoalMeasurement:
    with get_db() as conn:
      conn.execute(
        "INSERT INTO goal_measurements (goal_id, month, value, note) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(goal_id, month) DO UPDATE SET value=excluded.value, note=excluded.note",
        (goal_id, data.month, data.value, data.note),
      )
    return GoalMeasurement(goal_id=goal_id, **data.model_dump())

  def get_measurements(self, goal_id: int) -> list[GoalMeasurement]:
    with get_db() as conn:
      rows = conn.execute(
        "SELECT goal_id, month, value, note FROM goal_measurements WHERE goal_id = ? ORDER BY month ASC", (goal_id,)
      ).fetchall()
    return [GoalMeasurement(**row_to_dict(r)) for r in rows]

  def delete_measurement(self, goal_id: int, month: str) -> bool:
    with get_db() as conn:
      cursor = conn.execute("DELETE FROM goal_measurements WHERE goal_id = ? AND month = ?", (goal_id, month))
    return cursor.rowcount > 0

  def _to_snapshot(self, row) -> MonthlySnapshot:
    data = row_to_dict(row)
    return MonthlySnapshot(
      month=data["month"],
      status=data["status"],
      data_through=data["data_through"],
      metrics=json.loads(data["metrics_json"]),
      insights=json.loads(data["insights_json"]) if data["insights_json"] else None,
      schema_version=data["schema_version"],
      computed_at=data["computed_at"],
    )
