"""Test OpenRouterClient fast timeout and multi-model failover behavior."""

import time
from unittest.mock import MagicMock, patch

import httpx

from ai.openrouter_client import OpenRouterClient


def test_pick_next_free_model():
  client = OpenRouterClient(api_key="test", model="google/gemma-4-31b-it:free")
  tried = {"google/gemma-4-31b-it:free"}
  next_m = client._pick_next_free_model("google/gemma-4-31b-it:free", tried)
  assert next_m == "nvidia/nemotron-3-super-120b-a12b:free"

  tried.add("nvidia/nemotron-3-super-120b-a12b:free")
  next_m2 = client._pick_next_free_model(next_m, tried)
  assert next_m2 == "google/gemma-4-26b-a4b-it:free"


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


def test_free_only_replaces_paid_model(monkeypatch):
  monkeypatch.setenv("OPENROUTER_FREE_ONLY", "1")
  client = OpenRouterClient(api_key="test", model="anthropic/claude-sonnet-4")
  assert client.model.endswith(":free")
  assert OpenRouterClient(api_key="test", model="google/gemma-4-31b-it:free").model == "google/gemma-4-31b-it:free"


def test_paid_model_kept_without_free_only(monkeypatch):
  monkeypatch.delenv("OPENROUTER_FREE_ONLY", raising=False)
  assert OpenRouterClient(api_key="test", model="anthropic/claude-sonnet-4").model == "anthropic/claude-sonnet-4"


def test_complete_stops_when_time_budget_is_used_up():
  client = OpenRouterClient(api_key="test-key", model="google/gemma-4-31b-it:free")
  client.TOTAL_DEADLINE_SECONDS = 0

  with patch("httpx.Client.post", side_effect=AssertionError("must not call the network")):
    res = client.complete(system_prompt="You are a coach.", user_message="Hello", response_format={"type": "json_object"})

  assert res["error"] == "api_error"


def test_complete_gives_up_on_a_call_that_hangs():
  client = OpenRouterClient(api_key="test-key", model="google/gemma-4-31b-it:free")
  client.TOTAL_DEADLINE_SECONDS = 0.5

  def hanging_post(url, headers, json):
    time.sleep(2)

  started = time.time()
  with patch("httpx.Client.post", side_effect=hanging_post):
    res = client.complete(system_prompt="You are a coach.", user_message="Hello", response_format={"type": "json_object"})

  assert time.time() - started < 1.5
  assert res["error"] == "api_error"


def _capture_complete(model, temp_db):
  """Run complete() against a stubbed 200 reply and return the JSON payload that was sent."""
  client = OpenRouterClient(api_key="test-key", model=model)
  sent = {}
  reply = MagicMock()
  reply.status_code = 200
  reply.json.return_value = {"choices": [{"message": {"content": "ok"}}], "usage": {}}

  def capture_post(url, headers, json):
    sent.update(json)
    return reply

  with patch("httpx.Client.post", side_effect=capture_post):
    client.complete(system_prompt="You are a coach.", user_message="Hello")
  return client, sent


def test_paid_model_stays_pinned_and_uses_no_reasoning(temp_db):
  client, sent = _capture_complete("openai/gpt-6-luna", temp_db)

  assert sent["model"] == "openai/gpt-6-luna"
  assert sent["reasoning"] == {"effort": "none"}
  assert client._pick_next_free_model("openai/gpt-6-luna", {"openai/gpt-6-luna"}) is None


def test_free_model_sends_no_reasoning_field(temp_db):
  _, sent = _capture_complete("google/gemma-4-31b-it:free", temp_db)

  assert "reasoning" not in sent
