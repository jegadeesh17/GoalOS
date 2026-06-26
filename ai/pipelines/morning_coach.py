"""Morning mentor pipeline — one non-negotiable rule for today."""

from datetime import datetime, timezone

from ai.openrouter_client import OpenRouterClient
from ai.pipelines._base import fallback_morning, load_prompt
from services.mentor_briefing import format_briefing_for_prompt


def run_morning_coach(context: dict, client: OpenRouterClient = None) -> dict:
  client = client or OpenRouterClient()
  system = load_prompt("mentor")
  briefing = context.get("mentor_briefing", {})
  briefing_text = format_briefing_for_prompt(briefing) if briefing else ""

  user_msg = (
    f"{briefing_text}\n\n"
    "The user just submitted today's morning journal. "
    "Issue ONE mentor rule using ONLY the specifics above."
  )
  try:
    result = client.complete(
      system, user_msg,
      response_format={"type": "json_object"},
      temperature=0.45,
    )
    if isinstance(result, dict) and "error" not in result and result.get("mentor_rule"):
      result["source"] = "ai"
      result["model"] = client.model
      result["generated_at"] = datetime.now(timezone.utc).isoformat()
      return result
    fb = fallback_morning(context)
    if isinstance(result, dict) and result.get("error"):
      fb["fallback_reason"] = result["error"]
      fb["fallback_detail"] = result.get("error_detail", "")
    else:
      fb["fallback_reason"] = "invalid_response"
      fb["fallback_detail"] = "AI did not return a valid mentor rule"
    return fb
  except Exception as e:
    fb = fallback_morning(context)
    fb["fallback_reason"] = "api_error"
    fb["fallback_detail"] = str(e)
    return fb
