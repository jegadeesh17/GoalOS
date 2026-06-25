"""Journal import models."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class ParsedTask(BaseModel):
  text: str
  completed: bool = False


class ParsedTimeBlock(BaseModel):
  start: str
  end: str
  activity: str


class ParsedEntry(BaseModel):
  date: date
  gratitude: Optional[str] = None
  plans: list[ParsedTimeBlock] = Field(default_factory=list)
  tasks: list[ParsedTask] = Field(default_factory=list)
  review: Optional[str] = None
  takeaway: Optional[str] = None
  task_completion_rate: float = 0.0


class ImportResult(BaseModel):
  total_entries: int = 0
  successfully_imported: int = 0
  skipped_duplicates: int = 0
  errors: list[str] = Field(default_factory=list)
  memories_extracted: int = 0
  date_range: tuple[Optional[date], Optional[date]] = (None, None)
  onboarding_summary: str = ""
