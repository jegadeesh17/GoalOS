"""Goal model."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class GoalBase(BaseModel):
  title: str
  description: Optional[str] = None
  category: str
  horizon: str
  deadline: Optional[date] = None
  priority: int = Field(default=3, ge=1, le=5)
  progress: float = Field(default=0.0, ge=0.0, le=1.0)
  status: str = "active"
  reason: Optional[str] = None
  success_criteria: Optional[str] = None


class GoalCreate(GoalBase):
  pass


class GoalUpdate(BaseModel):
  title: Optional[str] = None
  description: Optional[str] = None
  category: Optional[str] = None
  horizon: Optional[str] = None
  deadline: Optional[date] = None
  priority: Optional[int] = Field(default=None, ge=1, le=5)
  progress: Optional[float] = Field(default=None, ge=0.0, le=1.0)
  status: Optional[str] = None
  reason: Optional[str] = None
  success_criteria: Optional[str] = None


class Goal(GoalBase):
  id: int
  created_at: Optional[datetime] = None
  updated_at: Optional[datetime] = None

  model_config = {"from_attributes": True}
