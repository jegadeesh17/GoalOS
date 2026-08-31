"""GoalOS domain-partitioned tool ecosystem."""

from __future__ import annotations

import json
from typing import Any, Optional

from ai.tools.calendar_toolkit import build_calendar_toolkit
from ai.tools.goals_toolkit import build_goals_toolkit
from ai.tools.journal_toolkit import build_journal_toolkit
from ai.tools.memory_toolkit import build_memory_toolkit
from ai.tools.registry import DomainToolkit, ToolDefinition, ToolRegistry
from database.repositories.goal_repository import GoalRepository
from services.memory_service import MemoryService

# Build default registry containing all domain-partitioned toolkits
_DEFAULT_REGISTRY = ToolRegistry()
_DEFAULT_REGISTRY.register_toolkit(build_memory_toolkit())
_DEFAULT_REGISTRY.register_toolkit(build_goals_toolkit())
_DEFAULT_REGISTRY.register_toolkit(build_journal_toolkit())
_DEFAULT_REGISTRY.register_toolkit(build_calendar_toolkit())

# Public schemas (includes legacy default set)
TOOL_DEFINITIONS: list[dict[str, Any]] = _DEFAULT_REGISTRY.get_schemas_for_domains(
  ["memory", "goals", "journal"]
)


def get_scoped_tool_definitions(domains: Optional[list[str]] = None) -> list[dict[str, Any]]:
  """Return tool definitions filtered to specific domain namespaces."""
  return _DEFAULT_REGISTRY.get_schemas_for_domains(domains)


def execute_tool(
  name: str,
  args: dict[str, Any],
  memory_service: Optional[MemoryService] = None,
  goal_repo: Optional[GoalRepository] = None,
  **kwargs: Any,
) -> dict[str, Any]:
  """Run a tool by name across all registered domain toolkits."""
  call_kwargs = dict(kwargs)
  if memory_service:
    call_kwargs["memory_service"] = memory_service
  if goal_repo:
    call_kwargs["goal_repo"] = goal_repo

  return _DEFAULT_REGISTRY.execute(name, args, **call_kwargs)


def make_tool_executor(
  memory_service: Optional[MemoryService] = None,
  goal_repo: Optional[GoalRepository] = None,
  domains: Optional[list[str]] = None,
):
  """Return a callable(name, args) for the OpenRouter tool loop."""

  def _run(name: str, args: dict[str, Any]) -> dict[str, Any]:
    return execute_tool(name, args, memory_service=memory_service, goal_repo=goal_repo)

  return _run


def serialize_tool_result(result: Any) -> str:
  return json.dumps(result, default=str)


def build_default_registry() -> ToolRegistry:
  return _DEFAULT_REGISTRY


__all__ = [
  "TOOL_DEFINITIONS",
  "ToolDefinition",
  "DomainToolkit",
  "ToolRegistry",
  "build_default_registry",
  "build_memory_toolkit",
  "build_goals_toolkit",
  "build_journal_toolkit",
  "build_calendar_toolkit",
  "get_scoped_tool_definitions",
  "execute_tool",
  "make_tool_executor",
  "serialize_tool_result",
]
