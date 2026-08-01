"""User domain model."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
  id: int = 1
  name: str = "User"
  life_vision: Optional[str] = None
  five_year_vision: Optional[str] = None
  one_year_vision: Optional[str] = None
  birth_date: str = "2002-06-17"
  target_age: int = 70
  created_at: Optional[datetime] = None
  updated_at: Optional[datetime] = None
