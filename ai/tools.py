"""LLM tool schemas and execution for GoalOS agent coaching."""

import json
from typing import Any, Optional

from database.repositories.goal_repository import GoalRepository
from services.memory_service import MemoryService

TOOL_DEFINITIONS: list[dict[str, Any]] = [
  {
    "type": "function",
    "function": {
      "name": "search_memories",
      "description": (
        "Search the user's past journal insights, lessons, and commitments "
        "using a semantic query. Use when you need relevant history for today's rule."
      ),
      "parameters": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "Natural-language search query (e.g. gym consistency, deep work)",
          },
        },
        "required": ["query"],
      },
    },
  },
  {
    "type": "function",
    "function": {
      "name": "get_active_goals",
      "description": "Return the user's currently active goals with title, category, and horizon.",
      "parameters": {"type": "object", "properties": {}},
    },
  },
]


def execute_tool(
  name: str,
  args: dict[str, Any],
  memory_service: Optional[MemoryService] = None,
  goal_repo: Optional[GoalRepository] = None,
) -> dict[str, Any]:
  """Run a tool by name. Reuses existing GoalOS services only."""
  memory_service = memory_service or MemoryService()
  goal_repo = goal_repo or GoalRepository()

  if name == "search_memories":
    query = str(args.get("query", "")).strip()
    if not query:
      return {"memories": [], "count": 0}
    memories = memory_service.retrieve(query, top_k=5)
    return {
      "memories": [
        {
          "text": m.text,
          "type": m.type,
          "importance": m.importance,
          "source_date": m.source_date.isoformat() if m.source_date else None,
        }
        for m in memories
      ],
      "count": len(memories),
    }

  if name == "get_active_goals":
    goals = goal_repo.get_active()
    return {
      "goals": [
        {
          "title": g.title,
          "category": g.category,
          "horizon": g.horizon,
          "priority": g.priority,
          "progress": g.progress,
        }
        for g in goals
      ],
      "count": len(goals),
    }

  return {"error": f"unknown_tool:{name}"}


def make_tool_executor(
  memory_service: Optional[MemoryService] = None,
  goal_repo: Optional[GoalRepository] = None,
):
  """Return a callable(name, args) for the OpenRouter tool loop."""

  def _run(name: str, args: dict[str, Any]) -> dict[str, Any]:
    return execute_tool(name, args, memory_service, goal_repo)

  return _run


def serialize_tool_result(result: Any) -> str:
  return json.dumps(result, default=str)
