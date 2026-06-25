"""Memory model."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class MemoryBase(BaseModel):
  text: str
  type: str
  importance: float = Field(default=0.5, ge=0.0, le=1.0)
  source_date: Optional[date] = None
  source_type: Optional[str] = None
  source_id: Optional[int] = None
  recency_score: Optional[float] = None
  access_count: int = 0
  last_accessed: Optional[datetime] = None


class MemoryCreate(MemoryBase):
  pass


class Memory(MemoryBase):
  id: int
  created_at: Optional[datetime] = None

  model_config = {"from_attributes": True}
