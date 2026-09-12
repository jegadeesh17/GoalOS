"""Test OpenRouterClient fast timeout and multi-model failover behavior."""

from unittest.mock import MagicMock, patch
import httpx

from ai.openrouter_client import OpenRouterClient


def test_pick_next_free_model():
  client = OpenRouterClient(api_key="test", model="google/gemma-4-31b-it:free")
  tried = {"google/gemma-4-31b-it:free"}
  next_m = client._pick_next_free_model("google/gemma-4-31b-it:free", tried)
  assert next_m == "google/gemma-4-26b-a4b-it:free"

  tried.add("google/gemma-4-26b-a4b-it:free")
  next_m2 = client._pick_next_free_model(next_m, tried)
  assert next_m2 == "nex-agi/nex-n2.5-pro:free"


def test_complete_failover_on_timeout():
  client = OpenRouterClient(api_key="test-key", model="google/gemma-4-31b-it:free")

  # Mock httpx.Client.post to timeout on first model, then succeed on fallback model
  mock_resp_success = MagicMock()
  mock_resp_success.status_code = 200
  mock_resp_success.json.return_value = {
    "choices": [{"message": {"content": "{\"mentor_rule\": \"Execute morning deep work first.\"}"}}],
    "usage": {"prompt_tokens": 10, "completion_tokens": 10},
  }

  def mock_post(url, headers, json):
    if json["model"] == "google/gemma-4-31b-it:free":
      raise httpx.ReadTimeout("Connection timed out")
    return mock_resp_success

  with patch("httpx.Client.post", side_effect=mock_post):
    res = client.complete(
      system_prompt="You are a coach.",
      user_message="Hello",
      response_format={"type": "json_object"},
      allow_fallback=True,
    )

  assert isinstance(res, dict)
  assert res.get("mentor_rule") == "Execute morning deep work first."


def test_complete_failover_on_502_error():
  client = OpenRouterClient(api_key="test-key", model="google/gemma-4-31b-it:free")

  mock_resp_502 = MagicMock()
  mock_resp_502.status_code = 502
  mock_resp_502.text = "Bad Gateway"

  mock_resp_success = MagicMock()
  mock_resp_success.status_code = 200
  mock_resp_success.json.return_value = {
    "choices": [{"message": {"content": "Hello from fallback model"}}],
    "usage": {"prompt_tokens": 5, "completion_tokens": 5},
  }

  def mock_post(url, headers, json):
    if json["model"] == "google/gemma-4-31b-it:free":
      return mock_resp_502
    return mock_resp_success

  with patch("httpx.Client.post", side_effect=mock_post):
    res = client.complete(
      system_prompt="System",
      user_message="User",
      allow_fallback=True,
    )

  assert res == "Hello from fallback model"
