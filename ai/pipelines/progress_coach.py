"""On-demand Progress Coaching Pipeline — Evaluates daily execution against 1-Month and 1-Year goals."""

from datetime import datetime, timezone

from ai.openrouter_client import OpenRouterClient
from ai.pipelines._base import fallback_progress, format_context, load_prompt


def run_progress_coach(context: dict, client: OpenRouterClient = None) -> dict:
  client = client or OpenRouterClient()
  system_prompt = (
    "You are GoalOS Lead Coach. Evaluate the user's current month progress, daily journal logs, "
    "and active 1-Month / 1-Year goals. Return JSON with keys:\n"
    "- pacing_status: string (e.g. 'On Track', 'Behind Schedule')\n"
    "- monthly_goal_evaluated: string\n"
    "- progress_narrative: string\n"
    "- key_wins_aligned: string\n"
    "- critical_bottleneck: string\n"
    "- actionable_coaching_advice: string\n"
  )

  formatted = format_context(context)
  user_msg = (
    f"User Progress & Goal Context:\n{formatted}\n\n"
    "Provide aggressive, high-clarity progress coaching evaluating how current month days logged "
    "and daily execution map to their 1-Month and 1-Year goals."
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
