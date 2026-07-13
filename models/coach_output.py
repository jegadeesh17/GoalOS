"""Validated public shape for morning coaching responses."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class CoachingEvidence(BaseModel):
  goal_id: int | None = None
  goal_title: str | None = None
  memory_id: int | None = None
  source_date: date | None = None


class MorningCoachOutput(BaseModel):
  mentor_rule: str = Field(min_length=1, max_length=600)
  why_this_rule: str = Field(default="", max_length=1200)
  past_mistake_called_out: str = Field(default="", max_length=1200)
  goal_connection: str = Field(default="", max_length=1200)
  if_you_ignore_this: str = Field(default="", max_length=1200)
  confidence: float = Field(default=0.0, ge=0.0, le=1.0)
  source: Literal["ai_agent", "ai", "personalized_fallback", "generic_fallback"] = "generic_fallback"
  fallback_reason: str | None = None
  fallback_detail: str | None = None
  model: str | None = None
  generated_at: str | None = None
  tools_used: list[str] = Field(default_factory=list)
  evidence: list[CoachingEvidence] = Field(default_factory=list)
