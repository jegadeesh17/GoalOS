"""Coach response model."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class CoachResponseBase(BaseModel):
  session_type: str
  user_message: Optional[str] = None
  ai_response: str
  date: date


class CoachResponseCreate(CoachResponseBase):
  pass


class CoachResponse(CoachResponseBase):
  id: int
  created_at: Optional[datetime] = None

  model_config = {"from_attributes": True}
