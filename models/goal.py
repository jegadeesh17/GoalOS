"""Goal model."""

import json
import re
from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

MIN_CUE_LENGTH = 3


def normalise_cues(value: Any) -> Optional[list[str]]:
  """Cues are words the user writes per goal so tasks can be matched to it. Stored normalised the same way
  as task keys (casefolded, punctuation-free, single-spaced); a cue shorter than 3 characters matches too
  much to mean anything, so it is rejected rather than silently dropped."""
  if value is None:
    return None
  if isinstance(value, str):
    try:
      value = json.loads(value)
    except json.JSONDecodeError:
      return None  # unreadable stored value: unknown, not an error for the whole goal
  cues: list[str] = []
  for raw in value:
    cue = " ".join(re.sub(r"[^\w\s]", " ", str(raw).casefold()).split())
    if not cue:
      continue
    if len(cue) < MIN_CUE_LENGTH:
      raise ValueError(f"Cue '{raw}' is too short: use at least {MIN_CUE_LENGTH} characters")
    if cue not in cues:
      cues.append(cue)
  return cues


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
  # Optional numeric target, checked in monthly (see YearlyPacingService). Unmeasured goals leave these empty.
  metric_name: Optional[str] = None
  metric_unit: Optional[str] = None
  start_value: Optional[float] = None
  target_value: Optional[float] = None
  # Words that mark a task as serving this goal (see services/task_link_service.py).
  cues: Optional[list[str]] = None

  _normalise_cues = field_validator("cues", mode="before")(normalise_cues)


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
  metric_name: Optional[str] = None
  metric_unit: Optional[str] = None
  start_value: Optional[float] = None
  target_value: Optional[float] = None
  cues: Optional[list[str]] = None

  _normalise_cues = field_validator("cues", mode="before")(normalise_cues)


class Goal(GoalBase):
  id: int
  created_at: Optional[datetime] = None
  updated_at: Optional[datetime] = None

  model_config = {"from_attributes": True}
