"""Goal alignment coaching pipeline."""

from ai.openrouter_client import OpenRouterClient
from ai.pipelines._base import fallback_goal_alignment, format_context, load_prompt


def run_goal_alignment_coach(context: dict, client: OpenRouterClient = None) -> dict:
  client = client or OpenRouterClient()
  system = load_prompt("goal_alignment")
  user_msg = f"Context:\n{format_context(context)}\n\nAnalyze goal alignment."
  try:
    result = client.complete(
      system, user_msg,
      response_format={"type": "json_object"},
      temperature=0.5,
    )
    if isinstance(result, dict) and "error" not in result:
      return result
  except Exception:
    pass
  return fallback_goal_alignment(context)
