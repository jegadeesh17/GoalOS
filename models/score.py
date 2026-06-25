"""Score model."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class ScoreBase(BaseModel):
  date: date
  scope: str
  goal_alignment_score: Optional[float] = None
  consistency_score: Optional[float] = None
  health_score: Optional[float] = None
  learning_score: Optional[float] = None
  productivity_score: Optional[float] = None
  momentum_score: Optional[float] = None
  overall_growth_score: Optional[float] = None
  gap_score: Optional[float] = None


class ScoreCreate(ScoreBase):
  pass


class Score(ScoreBase):
  id: int
  calculated_at: Optional[datetime] = None

  model_config = {"from_attributes": True}
