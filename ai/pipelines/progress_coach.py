"""On-demand Progress Coaching Pipeline — Evaluates daily execution against 1-Month and 1-Year goals."""

from datetime import datetime, timezone

from ai.openrouter_client import OpenRouterClient
from ai.pipelines._base import fallback_progress, format_context


def run_progress_coach(context: dict, client: OpenRouterClient = None) -> dict:
  client = client or OpenRouterClient()
  system_prompt = (
    "You are GoalOS Lead Coach. Evaluate the user's current month progress, multi-day journal logs, "
    "detected behavioral patterns, and active 1-Month / 1-Year goals.\n\n"
    "CRITICAL COACHING PRINCIPLE (PATTERNS OVER 1-DAY FRICTION):\n"
    "- Explicitly distinguish isolated single-day bad days (noise) from repeating unhealthy patterns (signal).\n"
    "- A repeating behavioral pattern (e.g. morning phone delay, recurring task rollover, afternoon slump) "
    "is the primary risk to achieving their 1-Month and 1-Year goals.\n"
    "- Provide an actionable pattern-breaking protocol that tackles the root trigger.\n\n"
    "Return JSON with keys:\n"
    "- pacing_status: string (e.g. 'On Track — High Execution', 'Behind Schedule — Repeating Pattern Detected')\n"
    "- monthly_goal_evaluated: string (target 1-Month goal)\n"
    "- progress_narrative: string (honest assessment of trajectory)\n"
    "- key_wins_aligned: string (compounding positive habits)\n"
    "- critical_bottleneck: string (the friction point)\n"
    "- recognized_pattern_analysis: string (analysis of repeating multi-day patterns vs isolated single-day noise with observed dates/counts)\n"
    "- actionable_pattern_breaking_protocol: string (tactical step-by-step countermeasure to dismantle the repeating loop)\n"
    "- actionable_coaching_advice: string (direct, high-clarity coaching directive)\n"
  )

  formatted = format_context(context)
  user_msg = (
    f"User Progress, Patterns & Goal Context:\n{formatted}\n\n"
    "Provide aggressive, high-clarity progress coaching evaluating how current month days logged "
    "and daily execution map to their 1-Month and 1-Year goals. Focus on repeating behavioral patterns over one-day friction."
  )

  try:
    result = client.complete(
      system_prompt,
      user_msg,
      response_format={"type": "json_object"},
      temperature=0.4,
    )
    if isinstance(result, dict) and "error" not in result and result.get("actionable_coaching_advice"):
      result["source"] = "ai"
      result["model"] = client.model
      result["generated_at"] = datetime.now(timezone.utc).isoformat()
      return result

    fb = fallback_progress(context)
    if isinstance(result, dict) and result.get("error"):
      fb["fallback_reason"] = result["error"]
      fb["fallback_detail"] = result.get("error_detail", "")
    return fb
  except Exception as exc:
    fb = fallback_progress(context)
    fb["fallback_reason"] = "api_error"
    fb["fallback_detail"] = str(exc)
    return fb
