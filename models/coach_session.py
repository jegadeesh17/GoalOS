"""Pydantic v2 models for multi-agent coordinator sessions, messages, and telemetry."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class CoachMessageRead(BaseModel):
  id: str
  session_id: str
  role: Literal["user", "assistant", "system"]
  content: str
  agent_name: Optional[str] = None
  tool_calls: list[dict[str, Any]] = Field(default_factory=list)
  citations: list[dict[str, Any]] = Field(default_factory=list)
  created_at: Optional[str] = None


class CoachSessionCreate(BaseModel):
  title: Optional[str] = None
  intent: Optional[str] = None
  active_horizon_id: Optional[str] = None
  blackboard: dict[str, Any] = Field(default_factory=dict)


class CoachSessionRead(BaseModel):
  id: str
  title: str
  intent: Optional[str] = None
  active_horizon_id: Optional[str] = None
  blackboard: dict[str, Any] = Field(default_factory=dict)
  created_at: Optional[str] = None
  updated_at: Optional[str] = None
  messages: list[CoachMessageRead] = Field(default_factory=list)


class CoachChatRequest(BaseModel):
  message: str = Field(min_length=1, max_length=4000)
  session_id: Optional[str] = None
  remote_ai_consent: bool = True
  preferred_domain: Optional[str] = None


class CoachChatResponse(BaseModel):
  session_id: str
  reply: str
  agent_name: str = "CoordinatorAgent"
  intent: str = "general_coaching"
  confidence: float = 0.85
  source: Literal["ai_agent", "deterministic_rules", "fallback"] = "ai_agent"
  tools_used: list[str] = Field(default_factory=list)
  citations: list[dict[str, Any]] = Field(default_factory=list)
  blackboard: dict[str, Any] = Field(default_factory=dict)
  trace_id: str
  latency_ms: float = 0.0
  fallback_reason: Optional[str] = None


class TelemetrySpan(BaseModel):
  id: Optional[int] = None
  trace_id: str
  span_name: str
  session_id: Optional[str] = None
  model: str
  prompt_tokens: int = 0
  completion_tokens: int = 0
  total_tokens: int = 0
  estimated_cost_usd: float = 0.0
  latency_ms: float = 0.0
  status: str = "success"
  error_message: Optional[str] = None
  created_at: Optional[str] = None


class TelemetrySummaryResponse(BaseModel):
  total_calls: int = 0
  total_tokens: int = 0
  prompt_tokens: int = 0
  completion_tokens: int = 0
  total_cost_usd: float = 0.0
  avg_latency_ms: float = 0.0
  p95_latency_ms: float = 0.0
  model_breakdown: dict[str, dict[str, Any]] = Field(default_factory=dict)
