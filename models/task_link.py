"""Task-to-goal link model."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, model_validator


class TaskLinkWrite(BaseModel):
  """A decision about one task wording: it serves a goal, or it was reviewed and serves none."""

  key: str
  kind: Literal["goal", "none"]
  goal_id: Optional[int] = None

  @model_validator(mode="after")
  def _goal_matches_kind(self) -> "TaskLinkWrite":
    if (self.kind == "goal") != (self.goal_id is not None):
      raise ValueError("goal_id is required for kind 'goal' and not allowed for kind 'none'")
    return self


class TaskLink(TaskLinkWrite):
  updated_at: Optional[datetime] = None
