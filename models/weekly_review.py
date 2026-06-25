"""Weekly review model."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class WeeklyReviewBase(BaseModel):
  week_start: date
  week_end: date
  ai_output: Optional[str] = None


class WeeklyReviewCreate(WeeklyReviewBase):
  pass


class WeeklyReview(WeeklyReviewBase):
  id: int
  created_at: Optional[datetime] = None

  model_config = {"from_attributes": True}
