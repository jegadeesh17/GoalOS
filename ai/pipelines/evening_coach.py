"""Evening coaching pipeline."""

from ai.openrouter_client import OpenRouterClient
from ai.pipelines._base import fallback_evening, format_context, load_prompt


def run_evening_coach(context: dict, client: OpenRouterClient = None) -> dict:
  client = client or OpenRouterClient()
  system = load_prompt("evening")
  user_msg = f"Context:\n{format_context(context)}\n\nProvide evening coaching based on today's journal."
  try:
    result = client.complete(
      system, user_msg,
      response_format={"type": "json_object"},
      temperature=0.7,
    )
    if isinstance(result, dict) and "error" not in result:
      return result
  except Exception:
    pass
  return fallback_evening(context)
