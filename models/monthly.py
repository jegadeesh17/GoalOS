"""Monthly analytics snapshot and goal-measurement models."""

from datetime import date, datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class MonthlySnapshot(BaseModel):
  """One stored month of derived analytics. Always recomputable from the daily logs."""

  month: str = Field(pattern=r"^\d{4}-\d{2}$")
  status: Literal["provisional", "final"]
  data_through: Optional[date] = None
  metrics: dict[str, Any]
  insights: Optional[dict[str, Any]] = None
  schema_version: int = 1
  computed_at: Optional[datetime] = None


class MonthlyGoalResult(BaseModel):
  """A goal's state as of the month's close (copied, so later edits cannot rewrite history)."""

  month: str
  goal_id: int
  goal_title: str
  horizon: str
  progress_at_close: Optional[float] = None
  status_at_close: Optional[str] = None
  as_of: date


class GoalMeasurementCreate(BaseModel):
  """A user-entered monthly check-in against a goal's numeric target."""

  month: str = Field(pattern=r"^\d{4}-\d{2}$")
  value: float
  note: Optional[str] = Field(default=None, max_length=500)


class GoalMeasurement(GoalMeasurementCreate):
  goal_id: int


class GoalPacePointCreate(BaseModel):
  """A point on the user's own expected path: "by this date I expect to be at this value"."""

  due: date
  value: float


class GoalPacePoint(GoalPacePointCreate):
  goal_id: int
