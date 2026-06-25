"""Reflection coaching pipeline."""

from ai.openrouter_client import OpenRouterClient
from ai.pipelines._base import fallback_reflection, format_context, load_prompt


def run_reflection_coach(context: dict, journal_text: str = "", client: OpenRouterClient = None) -> dict:
  client = client or OpenRouterClient()
  system = load_prompt("reflection")
  user_msg = f"Journal:\n{journal_text}\n\nContext:\n{format_context(context)}\n\nExtract insights."
  try:
    result = client.complete(
      system, user_msg,
      response_format={"type": "json_object"},
      temperature=0.6,
    )
    if isinstance(result, dict) and "error" not in result:
      return result
  except Exception:
    pass
  return fallback_reflection(context)
