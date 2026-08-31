"""Repository for AI telemetry, token usage, latency, and cost tracking."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from database.connection import get_db
from database.repositories._helpers import row_to_dict
from models.coach_session import TelemetrySpan, TelemetrySummaryResponse


class TelemetryRepository:
  """Persistence and aggregation for AI execution metrics and spend."""

  def record_span(
    self,
    trace_id: str,
    span_name: str,
    model: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int = 0,
    estimated_cost_usd: float = 0.0,
    latency_ms: float = 0.0,
    session_id: Optional[str] = None,
    status: str = "success",
    error_message: Optional[str] = None,
  ) -> TelemetrySpan:
    now = datetime.now(timezone.utc).isoformat()
    if total_tokens == 0:
      total_tokens = prompt_tokens + completion_tokens

    with get_db() as conn:
      cursor = conn.execute(
        """
        INSERT INTO ai_telemetry (
          trace_id, span_name, session_id, model,
          prompt_tokens, completion_tokens, total_tokens,
          estimated_cost_usd, latency_ms, status, error_message, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
          trace_id,
          span_name,
          session_id,
          model,
          prompt_tokens,
          completion_tokens,
          total_tokens,
          estimated_cost_usd,
          latency_ms,
          status,
          error_message,
          now,
        ),
      )
      rec_id = cursor.lastrowid

    return TelemetrySpan(
      id=rec_id,
      trace_id=trace_id,
      span_name=span_name,
      session_id=session_id,
      model=model,
      prompt_tokens=prompt_tokens,
      completion_tokens=completion_tokens,
      total_tokens=total_tokens,
      estimated_cost_usd=estimated_cost_usd,
      latency_ms=latency_ms,
      status=status,
      error_message=error_message,
      created_at=now,
    )

  def get_summary(self, days: int = 30) -> TelemetrySummaryResponse:
    with get_db() as conn:
      rows = conn.execute(
        """
        SELECT
          model,
          COUNT(*) as call_count,
          SUM(prompt_tokens) as sum_prompt,
          SUM(completion_tokens) as sum_comp,
          SUM(total_tokens) as sum_total,
          SUM(estimated_cost_usd) as sum_cost,
          AVG(latency_ms) as avg_lat
        FROM ai_telemetry
        WHERE created_at >= datetime('now', ?)
        GROUP BY model
        """,
        (f"-{days} days",),
      ).fetchall()

      lat_rows = conn.execute(
        """
        SELECT latency_ms FROM ai_telemetry
        WHERE created_at >= datetime('now', ?) AND status = 'success'
        ORDER BY latency_ms ASC
        """,
        (f"-{days} days",),
      ).fetchall()

    total_calls = 0
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    total_cost_usd = 0.0
    model_breakdown: dict[str, dict[str, Any]] = {}

    for r in rows:
      r_dict = row_to_dict(r)
      m_name = r_dict["model"] or "unknown"
      c_count = r_dict["call_count"] or 0
      p_tok = r_dict["sum_prompt"] or 0
      c_tok = r_dict["sum_comp"] or 0
      t_tok = r_dict["sum_total"] or 0
      cost = r_dict["sum_cost"] or 0.0
      avg_lat = r_dict["avg_lat"] or 0.0

      total_calls += c_count
      prompt_tokens += p_tok
      completion_tokens += c_tok
      total_tokens += t_tok
      total_cost_usd += cost

      model_breakdown[m_name] = {
        "call_count": c_count,
        "prompt_tokens": p_tok,
        "completion_tokens": c_tok,
        "total_tokens": t_tok,
        "estimated_cost_usd": round(cost, 6),
        "avg_latency_ms": round(avg_lat, 2),
      }

    latencies = [row_to_dict(lr)["latency_ms"] for lr in lat_rows]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    p95_idx = int(len(latencies) * 0.95)
    p95_latency = latencies[p95_idx] if latencies and p95_idx < len(latencies) else (latencies[-1] if latencies else 0.0)

    return TelemetrySummaryResponse(
      total_calls=total_calls,
      total_tokens=total_tokens,
      prompt_tokens=prompt_tokens,
      completion_tokens=completion_tokens,
      total_cost_usd=round(total_cost_usd, 6),
      avg_latency_ms=round(avg_latency, 2),
      p95_latency_ms=round(p95_latency, 2),
      model_breakdown=model_breakdown,
    )

  def get_recent_traces(self, limit: int = 25) -> list[TelemetrySpan]:
    with get_db() as conn:
      rows = conn.execute(
        "SELECT * FROM ai_telemetry ORDER BY created_at DESC LIMIT ?", (limit,)
      ).fetchall()

    return [
      TelemetrySpan(
        id=r["id"],
        trace_id=r["trace_id"],
        span_name=r["span_name"],
        session_id=r["session_id"],
        model=r["model"],
        prompt_tokens=r["prompt_tokens"],
        completion_tokens=r["completion_tokens"],
        total_tokens=r["total_tokens"],
        estimated_cost_usd=round(r["estimated_cost_usd"] or 0.0, 6),
        latency_ms=round(r["latency_ms"] or 0.0, 2),
        status=r["status"],
        error_message=r["error_message"],
        created_at=str(r["created_at"] or ""),
      )
      for r in rows
    ]
