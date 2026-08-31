"""Observability & Telemetry service for AI execution traces, latency, and cost tracking."""

from __future__ import annotations

import time
import uuid
from typing import Any, Optional

from database.repositories.telemetry_repository import TelemetryRepository
from models.coach_session import TelemetrySpan, TelemetrySummaryResponse

# Pricing table per 1 Million tokens (Prompt USD, Completion USD)
MODEL_PRICING_PER_1M: dict[str, tuple[float, float]] = {
  # Free tier models
  "free": (0.0, 0.0),
  # Anthropic
  "anthropic/claude-3.5-sonnet": (3.00, 15.00),
  "anthropic/claude-3.7-sonnet": (3.00, 15.00),
  "anthropic/claude-3-5-haiku": (0.80, 4.00),
  "anthropic/claude-3-haiku": (0.25, 1.25),
  # Google
  "google/gemini-2.5-flash": (0.10, 0.40),
  "google/gemini-2.0-flash": (0.10, 0.40),
  "google/gemini-flash-1.5": (0.075, 0.30),
  "google/gemini-pro-1.5": (1.25, 5.00),
  # Meta & Open Source
  "meta-llama/llama-3.3-70b-instruct": (0.13, 0.40),
  "meta-llama/llama-3.1-8b-instruct": (0.05, 0.05),
  "mistralai/mistral-large": (2.00, 6.00),
  "deepseek/deepseek-chat": (0.14, 0.28),
  "deepseek/deepseek-r1": (0.55, 2.19),
  # OpenAI
  "openai/gpt-4o": (2.50, 10.00),
  "openai/gpt-4o-mini": (0.15, 0.60),
}


class ObservabilityService:
  """Centralized APM telemetry and AI cost calculation engine."""

  def __init__(self, telemetry_repo: Optional[TelemetryRepository] = None) -> None:
    self.repo = telemetry_repo or TelemetryRepository()

  @staticmethod
  def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate approximate USD cost for token usage."""
    if not model or ":free" in model.lower() or model.lower().endswith("/free"):
      return 0.0

    matched_key = None
    for key in MODEL_PRICING_PER_1M:
      if key in model.lower():
        matched_key = key
        break

    if matched_key:
      prompt_rate, comp_rate = MODEL_PRICING_PER_1M[matched_key]
    else:
      # Default fallback estimate ($0.50 / $1.50 per 1M)
      prompt_rate, comp_rate = (0.50, 1.50)

    prompt_cost = (prompt_tokens / 1_000_000.0) * prompt_rate
    comp_cost = (completion_tokens / 1_000_000.0) * comp_rate
    return round(prompt_cost + comp_cost, 6)

  def record_span(
    self,
    span_name: str,
    model: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    latency_ms: float = 0.0,
    trace_id: Optional[str] = None,
    session_id: Optional[str] = None,
    status: str = "success",
    error_message: Optional[str] = None,
  ) -> TelemetrySpan:
    """Record an individual execution span into telemetry database."""
    tid = trace_id or f"tr_{uuid.uuid4().hex[:12]}"
    cost_usd = self.calculate_cost(model, prompt_tokens, completion_tokens)
    total_tokens = prompt_tokens + completion_tokens

    return self.repo.record_span(
      trace_id=tid,
      span_name=span_name,
      session_id=session_id,
      model=model,
      prompt_tokens=prompt_tokens,
      completion_tokens=completion_tokens,
      total_tokens=total_tokens,
      estimated_cost_usd=cost_usd,
      latency_ms=latency_ms,
      status=status,
      error_message=error_message,
    )

  def get_summary(self, days: int = 30) -> TelemetrySummaryResponse:
    """Fetch aggregated token usage and cost metrics."""
    return self.repo.get_summary(days=days)

  def get_recent_traces(self, limit: int = 25) -> list[TelemetrySpan]:
    """Fetch recent telemetry spans."""
    return self.repo.get_recent_traces(limit=limit)
