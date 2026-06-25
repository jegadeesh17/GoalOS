"""Daily log model."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class DailyLogBase(BaseModel):
  date: date
  morning_completed: bool = False
  sleep_hours: Optional[float] = None
  sleep_quality: Optional[int] = Field(default=None, ge=1, le=5)
  energy_level: Optional[int] = Field(default=None, ge=1, le=5)
  mood_morning: Optional[int] = Field(default=None, ge=1, le=5)
  expected_focus: Optional[int] = Field(default=None, ge=1, le=5)
  available_hours: Optional[float] = None
  calendar_constraints: Optional[str] = None
  free_write: Optional[str] = None
  intention: Optional[str] = None
  anxiety: Optional[str] = None
  anticipation: Optional[str] = None
  top_priority: Optional[str] = None
  supporting_task_1: Optional[str] = None
  supporting_task_2: Optional[str] = None
  gratitude: Optional[str] = None
  time_blocks: Optional[str] = None
  planned_tasks: Optional[str] = None
  evening_completed: bool = False
  journal_entry: Optional[str] = None
  tasks_completed: Optional[str] = None
  task_completion_rate: Optional[float] = None
  deep_work_hours: Optional[float] = None
  workout_completed: Optional[bool] = None
  workout_notes: Optional[str] = None
  biggest_distraction: Optional[str] = None
  mood_evening: Optional[int] = Field(default=None, ge=1, le=5)
  one_win: Optional[str] = None
  one_lesson: Optional[str] = None
  takeaway: Optional[str] = None
  morning_ai_output: Optional[str] = None
  evening_ai_output: Optional[str] = None
  imported: bool = False
  import_source: Optional[str] = None


class DailyLogCreate(DailyLogBase):
  pass


class DailyLogUpdate(BaseModel):
  morning_completed: Optional[bool] = None
  sleep_hours: Optional[float] = None
  sleep_quality: Optional[int] = Field(default=None, ge=1, le=5)
  energy_level: Optional[int] = Field(default=None, ge=1, le=5)
  mood_morning: Optional[int] = Field(default=None, ge=1, le=5)
  expected_focus: Optional[int] = Field(default=None, ge=1, le=5)
  available_hours: Optional[float] = None
  calendar_constraints: Optional[str] = None
  free_write: Optional[str] = None
  intention: Optional[str] = None
  anxiety: Optional[str] = None
  anticipation: Optional[str] = None
  top_priority: Optional[str] = None
  supporting_task_1: Optional[str] = None
  supporting_task_2: Optional[str] = None
  gratitude: Optional[str] = None
  time_blocks: Optional[str] = None
  planned_tasks: Optional[str] = None
  evening_completed: Optional[bool] = None
  journal_entry: Optional[str] = None
  tasks_completed: Optional[str] = None
  task_completion_rate: Optional[float] = None
  deep_work_hours: Optional[float] = None
  workout_completed: Optional[bool] = None
  workout_notes: Optional[str] = None
  biggest_distraction: Optional[str] = None
  mood_evening: Optional[int] = Field(default=None, ge=1, le=5)
  one_win: Optional[str] = None
  one_lesson: Optional[str] = None
  takeaway: Optional[str] = None
  morning_ai_output: Optional[str] = None
  evening_ai_output: Optional[str] = None
  imported: Optional[bool] = None
  import_source: Optional[str] = None


class DailyLog(DailyLogBase):
  id: int
  created_at: Optional[datetime] = None
  updated_at: Optional[datetime] = None

  model_config = {"from_attributes": True}
