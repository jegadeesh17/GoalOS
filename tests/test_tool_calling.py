"""Tests for LLM tool definitions and execution."""

import json
from unittest.mock import MagicMock, patch

from ai.tools import TOOL_DEFINITIONS, execute_tool, make_tool_executor
from models.goal import GoalCreate
from models.memory import MemoryCreate


def test_tool_definitions_has_expected_tools():
  names = {t["function"]["name"] for t in TOOL_DEFINITIONS}
  assert {"search_memories", "get_active_goals", "get_monthly_progress"}.issubset(names)


def test_execute_search_memories(temp_db):
  from database.repositories.memory_repository import MemoryRepository
  from services.memory_service import MemoryService

  repo = MemoryRepository()
  repo.create(MemoryCreate(text="Gym consistency matters", type="commitment", importance=0.8))
  ms = MemoryService()
  result = execute_tool("search_memories", {"query": "gym"}, memory_service=ms)
  assert result["count"] >= 1
  assert "gym" in result["memories"][0]["text"].lower()


def test_execute_get_active_goals(temp_db):
  from database.repositories.goal_repository import GoalRepository

  repo = GoalRepository()
  repo.create(GoalCreate(title="Ship GoalOS", category="career", horizon="quarterly"))
  result = execute_tool("get_active_goals", {}, goal_repo=repo)
  assert result["count"] == 1
  assert result["goals"][0]["title"] == "Ship GoalOS"


def test_execute_unknown_tool():
  result = execute_tool("nonexistent", {})
  assert "error" in result


def test_complete_with_tools_loop():
  from ai.openrouter_client import OpenRouterClient

  tool_response = {
    "choices": [{
      "message": {
        "role": "assistant",
        "tool_calls": [{
          "id": "call_1",
          "type": "function",
          "function": {
            "name": "get_active_goals",
            "arguments": "{}",
          },
        }],
      },
    }],
  }
  final_response = {
    "choices": [{
      "message": {
        "role": "assistant",
        "content": json.dumps({
          "mentor_rule": "Do deep work first.",
          "why_this_rule": "Goals need focus.",
          "past_mistake_called_out": "Distraction",
          "goal_connection": "Career",
          "if_you_ignore_this": "Slip",
          "confidence": 0.9,
        }),
      },
    }],
  }

  client = OpenRouterClient(api_key="test-key", model="test-model")
  mock_post = MagicMock()
  mock_post.side_effect = [
    MagicMock(status_code=200, json=lambda: tool_response, raise_for_status=lambda: None),
    MagicMock(status_code=200, json=lambda: final_response, raise_for_status=lambda: None),
  ]

  executor = make_tool_executor(goal_repo=MagicMock(get_active=MagicMock(return_value=[])))

  with patch("httpx.Client") as mock_client_cls:
    mock_client_cls.return_value.__enter__.return_value.post = mock_post
    result = client.complete_with_tools(
      "system",
      "user",
      tools=TOOL_DEFINITIONS,
      tool_executor=executor,
      response_format={"type": "json_object"},
    )

  assert result["mentor_rule"] == "Do deep work first."
  assert result["tool_calls_made"] == ["get_active_goals"]
  assert mock_post.call_count == 2
