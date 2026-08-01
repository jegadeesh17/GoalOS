"""OpenRouter LLM client with retry and JSON parsing."""

import json
import logging
import time
from typing import Any, Callable, Optional, Union

import httpx

from config.settings import settings

logger = logging.getLogger(__name__)


class OpenRouterClient:
  """Client for OpenRouter API."""

  BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
  FREE_FALLBACK_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "openai/gpt-oss-20b:free",
    "qwen/qwen3-coder:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "google/gemma-4-31b-it:free",
    "cohere/north-mini-code:free",
  ]

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
      if reply.strip().startswith("Error:"):
        raw = reply.strip()[len("Error:"):].strip()
        if "—" in raw:
          code, detail = raw.split("—", 1)
          return {"ok": False, "error": code.strip(), "detail": detail.strip()}
        return {"ok": False, "error": "api_error", "detail": reply.strip()}
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

    current_model = self.model
    tried_models = {current_model}

    last_error = None
    last_status_code: Optional[int] = None
    last_response_text: str = ""
    for attempt in range(max_retries):
      start = time.time()
      try:
        payload["model"] = current_model
        with httpx.Client(timeout=60.0) as client:
          response = client.post(self.BASE_URL, headers=headers, json=payload)
          latency = time.time() - start
          logger.info(
            "OpenRouter request completed in %.2fs (attempt %d, model=%s)",
            latency,
            attempt + 1,
            current_model,
          )

          if response.status_code == 401:
            return self._error_response("invalid_api_key", "Key rejected by OpenRouter", response_format)
          if response.status_code == 402:
            free_model = self._pick_next_free_model(current_model, tried_models)
            if free_model:
              logger.warning(
                "Insufficient credits on %s. Retrying with free model %s.",
                current_model,
                free_model,
              )
              current_model = free_model
              tried_models.add(current_model)
              continue
            return self._error_response("insufficient_credits", "Add credits at openrouter.ai", response_format)
          if response.status_code == 404:
            free_model = self._pick_next_free_model(current_model, tried_models)
            if free_model:
              logger.warning(
                "Model %s not found. Retrying with free model %s.",
                current_model,
                free_model,
              )
              current_model = free_model
              tried_models.add(current_model)
              continue
            return self._error_response("model_not_found", f"Model not found: {current_model}", response_format)

          if response.status_code in (429, 500, 502, 503):
            last_status_code = response.status_code
            last_response_text = response.text or ""
            if response.status_code == 429:
              free_model = self._pick_next_free_model(current_model, tried_models)
              if free_model:
                logger.warning(
                  "Model %s is rate-limited. Retrying with free model %s.",
                  current_model,
                  free_model,
                )
                current_model = free_model
                tried_models.add(current_model)
                continue
            wait = 2 ** attempt
            logger.warning("Rate limited/server error %d, retrying in %ds", response.status_code, wait)
            time.sleep(wait)
            continue

          response.raise_for_status()
          data = response.json()
          raw_content = data["choices"][0]["message"].get("content", "")
          content = self._extract_text_content(raw_content)
          if not content.strip():
            free_model = self._pick_next_free_model(current_model, tried_models)
            if free_model:
              logger.warning(
                "Model %s returned empty content. Retrying with %s.",
                current_model,
                free_model,
              )
              current_model = free_model
              tried_models.add(current_model)
              continue

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
    if last_status_code == 429:
      return self._error_response(
        "rate_limited",
        "Free model is currently rate-limited. Try again in 1-2 minutes or switch to another :free model.",
        response_format,
      )
    if last_status_code in (500, 502, 503):
      return self._error_response(
        "server_unavailable",
        f"OpenRouter temporary server issue ({last_status_code}). Please retry shortly.",
        response_format,
      )
    if last_status_code and last_response_text:
      return self._error_response(
        "api_error",
        f"HTTP {last_status_code}: {last_response_text[:300]}",
        response_format,
      )
    return self._error_response("api_error", str(last_error) if last_error else "Unknown error", response_format)

  def complete_with_tools(
    self,
    system_prompt: str,
    user_message: str,
    tools: list[dict[str, Any]],
    tool_executor: Callable[[str, dict[str, Any]], Any],
    response_format: Optional[dict] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    max_tool_rounds: int = 3,
    max_retries: int = 3,
  ) -> Union[dict, str]:
    """LLM completion with OpenAI-style tool / function calling loop."""
    from ai.tools import serialize_tool_result

    if not self.api_key:
      logger.warning("No OpenRouter API key configured")
      return self._error_response("no_api_key", "Set OPENROUTER_API_KEY in .env", response_format)

    headers = {
      "Authorization": f"Bearer {self.api_key}",
      "Content-Type": "application/json",
      "HTTP-Referer": "https://goalos.local",
      "X-Title": "GoalOS",
    }
    messages: list[dict[str, Any]] = [
      {"role": "system", "content": system_prompt},
      {"role": "user", "content": user_message},
    ]
    tools_used: list[str] = []
    current_model = self.model

    for _round in range(max_tool_rounds):
      payload: dict[str, Any] = {
        "model": current_model,
        "messages": messages,
        "tools": tools,
        "temperature": temperature,
        "max_tokens": max_tokens,
      }
      if response_format and _round == max_tool_rounds - 1:
        payload["response_format"] = response_format

      data = self._post_chat_completion(headers, payload, max_retries)
      if isinstance(data, dict) and data.get("error"):
        return data

      message = data["choices"][0]["message"]
      tool_calls = message.get("tool_calls")

      if tool_calls:
        messages.append(message)
        for tc in tool_calls:
          fn = tc.get("function", {})
          name = fn.get("name", "")
          try:
            args = json.loads(fn.get("arguments") or "{}")
          except json.JSONDecodeError:
            args = {}
          tools_used.append(name)
          result = tool_executor(name, args)
          messages.append({
            "role": "tool",
            "tool_call_id": tc.get("id", name),
            "content": serialize_tool_result(result),
          })
        continue

      raw_content = message.get("content", "")
      content = self._extract_text_content(raw_content)
      if response_format:
        parsed = self._parse_json(content)
        if isinstance(parsed, dict):
          parsed["tool_calls_made"] = tools_used
        return parsed
      return content

    return self._error_response(
      "tool_loop_exhausted",
      f"Exceeded {max_tool_rounds} tool rounds",
      response_format,
    )

  def _post_chat_completion(
    self,
    headers: dict[str, str],
    payload: dict[str, Any],
    max_retries: int,
  ) -> dict[str, Any]:
    """POST chat/completions and return parsed JSON body or error dict."""
    current_model = payload.get("model", self.model)
    tried_models = {current_model}
    last_error = None
    last_status_code: Optional[int] = None

    for attempt in range(max_retries):
      payload["model"] = current_model
      try:
        with httpx.Client(timeout=60.0) as client:
          response = client.post(self.BASE_URL, headers=headers, json=payload)
          if response.status_code == 401:
            return {"error": "invalid_api_key", "error_detail": "Key rejected by OpenRouter"}
          if response.status_code == 402:
            free_model = self._pick_next_free_model(current_model, tried_models)
            if free_model:
              current_model = free_model
              tried_models.add(current_model)
              continue
            return {"error": "insufficient_credits", "error_detail": "Add credits at openrouter.ai"}
          if response.status_code == 404:
            free_model = self._pick_next_free_model(current_model, tried_models)
            if free_model:
              current_model = free_model
              tried_models.add(current_model)
              continue
            return {"error": "model_not_found", "error_detail": f"Model not found: {current_model}"}
          if response.status_code in (429, 500, 502, 503):
            last_status_code = response.status_code
            if response.status_code == 429:
              free_model = self._pick_next_free_model(current_model, tried_models)
              if free_model:
                current_model = free_model
                tried_models.add(current_model)
                continue
            time.sleep(2 ** attempt)
            continue
          response.raise_for_status()
          return response.json()
      except Exception as e:
        last_error = e
        if attempt < max_retries - 1:
          time.sleep(2 ** attempt)

    if last_status_code == 429:
      return {
        "error": "rate_limited",
        "error_detail": "Model rate-limited. Retry shortly or switch model.",
      }
    return {
      "error": "api_error",
      "error_detail": str(last_error) if last_error else "Unknown error",
    }

  def _error_response(self, code: str, detail: str, response_format: Optional[dict]) -> Union[dict, str]:
    if response_format:
      return {"error": code, "error_detail": detail, "confidence": 0.0}
    return f"Error: {code} — {detail}"

  def _pick_next_free_model(self, current_model: str, tried_models: set[str]) -> Optional[str]:
    """Choose next untried free model."""
    for model in self.FREE_FALLBACK_MODELS:
      if model != current_model and model not in tried_models:
        return model
    return None

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

  def _extract_text_content(self, content: Any) -> str:
    """Normalize OpenRouter content payload to plain text."""
    if isinstance(content, str):
      return content
    if isinstance(content, list):
      text_parts: list[str] = []
      for part in content:
        if isinstance(part, dict):
          if part.get("type") == "text" and part.get("text"):
            text_parts.append(str(part["text"]))
          elif part.get("text"):
            text_parts.append(str(part["text"]))
        elif part:
          text_parts.append(str(part))
      return "\n".join(p for p in text_parts if p).strip()
    return str(content or "")
