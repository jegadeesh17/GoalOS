"""Future self coaching pipeline."""

from ai.openrouter_client import OpenRouterClient
from ai.pipelines._base import fallback_future_self, format_context, load_prompt


def run_future_self_coach(context: dict, client: OpenRouterClient = None) -> dict:
  client = client or OpenRouterClient()
  system = load_prompt("future_self")
  user_msg = f"Context:\n{format_context(context)}\n\nWrite as the user's future self."
  try:
    result = client.complete(
      system, user_msg,
      response_format={"type": "json_object"},
      temperature=0.8,
    )
    if isinstance(result, dict) and "error" not in result:
      return result
  except Exception:
    pass
  return fallback_future_self(context)
