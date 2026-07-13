"""Milestone models linked to long-term goals."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class MilestoneBase(BaseModel):
  goal_id: int
  title: str = Field(min_length=1, max_length=240)
  success_criteria: Optional[str] = Field(default=None, max_length=2000)
  deadline: Optional[date] = None
  progress: float = Field(default=0.0, ge=0.0, le=1.0)
  status: str = Field(default="active", pattern="^(active|completed|archived)$")


class MilestoneCreate(MilestoneBase):
  pass


class MilestoneUpdate(BaseModel):
  title: Optional[str] = Field(default=None, min_length=1, max_length=240)
  success_criteria: Optional[str] = Field(default=None, max_length=2000)
  deadline: Optional[date] = None
  progress: Optional[float] = Field(default=None, ge=0.0, le=1.0)
  status: Optional[str] = Field(default=None, pattern="^(active|completed|archived)$")


class Milestone(MilestoneBase):
  id: int
  created_at: Optional[datetime] = None
  updated_at: Optional[datetime] = None

  model_config = {"from_attributes": True}
