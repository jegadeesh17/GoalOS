"""Weekly coaching pipeline."""

from ai.openrouter_client import OpenRouterClient
from ai.pipelines._base import fallback_weekly, format_context, load_prompt


def run_weekly_coach(context: dict, client: OpenRouterClient = None) -> dict:
  client = client or OpenRouterClient()
  system = load_prompt("weekly")
  user_msg = f"Context:\n{format_context(context)}\n\nProvide weekly review coaching."
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
  return fallback_weekly(context)
