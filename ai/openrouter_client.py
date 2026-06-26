"""OpenRouter LLM client with retry and JSON parsing."""

import json
import logging
import time
from typing import Any, Optional, Union

import httpx

from config.settings import settings

logger = logging.getLogger(__name__)


class OpenRouterClient:
  """Client for OpenRouter API."""

  BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

  def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
    self.api_key = api_key or settings.OPENROUTER_API_KEY
    self.model = model or settings.OPENROUTER_MODEL

  def refresh_config(self) -> None:
    """Reload API key and model from .env (after Settings save)."""
    import os
    from dotenv import load_dotenv
    from config.settings import _BASE_DIR
    load_dotenv(_BASE_DIR / ".env", override=True)
    self.api_key = os.getenv("OPENROUTER_API_KEY", "") or ""
    self.model = os.getenv("OPENROUTER_MODEL", self.model) or self.model

  def test_connection(self) -> dict:
    """Quick ping to verify OpenRouter key + model work."""
    if not self.api_key:
      return {"ok": False, "error": "no_api_key", "detail": "No API key in .env or Settings"}
    reply = self.complete(
      "You are a connection test. Reply with exactly: OK",
      "Test",
      temperature=0,
      max_tokens=16,
    )
    if isinstance(reply, str) and reply.strip():
      return {"ok": True, "model": self.model, "reply": reply.strip()[:80]}
    if isinstance(reply, dict) and reply.get("error"):
      return {"ok": False, "error": reply["error"], "detail": reply.get("error_detail", "")}
    return {"ok": False, "error": "empty_response", "detail": "Model returned nothing"}

  def complete(
    self,
    system_prompt: str,
    user_message: str,
    response_format: Optional[dict] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    max_retries: int = 3,
  ) -> Union[dict, str]:
    """Call OpenRouter with retry logic."""
    if not self.api_key:
      logger.warning("No OpenRouter API key configured")
      return self._error_response("no_api_key", "Set OPENROUTER_API_KEY in .env", response_format)

    headers = {
      "Authorization": f"Bearer {self.api_key}",
      "Content-Type": "application/json",
      "HTTP-Referer": "https://goalos.local",
      "X-Title": "GoalOS",
    }
    payload: dict[str, Any] = {
      "model": self.model,
      "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
      ],
      "temperature": temperature,
      "max_tokens": max_tokens,
    }
    if response_format:
      payload["response_format"] = response_format

    last_error = None
    for attempt in range(max_retries):
      start = time.time()
      try:
        with httpx.Client(timeout=60.0) as client:
          response = client.post(self.BASE_URL, headers=headers, json=payload)
          latency = time.time() - start
          logger.info("OpenRouter request completed in %.2fs (attempt %d)", latency, attempt + 1)

          if response.status_code == 401:
            return self._error_response("invalid_api_key", "Key rejected by OpenRouter", response_format)
          if response.status_code == 402:
            return self._error_response("insufficient_credits", "Add credits at openrouter.ai", response_format)
          if response.status_code == 404:
            return self._error_response("model_not_found", f"Model not found: {self.model}", response_format)

          if response.status_code in (429, 500, 502, 503):
            wait = 2 ** attempt
            logger.warning("Rate limited/server error %d, retrying in %ds", response.status_code, wait)
            time.sleep(wait)
            continue

          response.raise_for_status()
          data = response.json()
          content = data["choices"][0]["message"]["content"]

          if response_format:
            return self._parse_json(content)
          return content

      except Exception as e:
        last_error = e
        wait = 2 ** attempt
        logger.error("OpenRouter error (attempt %d): %s", attempt + 1, e)
        if attempt < max_retries - 1:
          time.sleep(wait)

    logger.error("All retries failed: %s", last_error)
    return self._error_response("api_error", str(last_error) if last_error else "Unknown error", response_format)

  def _error_response(self, code: str, detail: str, response_format: Optional[dict]) -> Union[dict, str]:
    if response_format:
      return {"error": code, "error_detail": detail, "confidence": 0.0}
    return f"Error: {code} — {detail}"

  def _parse_json(self, content: str) -> dict:
    content = content.strip()
    if content.startswith("```"):
      content = content.split("```")[1]
      if content.startswith("json"):
        content = content[4:]
    try:
      return json.loads(content)
    except json.JSONDecodeError:
      start = content.find("{")
      end = content.rfind("}") + 1
      if start >= 0 and end > start:
        return json.loads(content[start:end])
      raise
