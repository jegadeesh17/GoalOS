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
      return self._fallback_response(response_format)

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
    return self._fallback_response(response_format)

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

  def _fallback_response(self, response_format: Optional[dict]) -> Union[dict, str]:
    if response_format:
      return {"error": "LLM unavailable", "confidence": 0.0}
    return "I'm temporarily unavailable. Please try again later."
