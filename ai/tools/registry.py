"""Base classes and registry for domain-partitioned agent tools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class ToolDefinition:
  name: str
  description: str
  parameters: dict[str, Any]
  handler: Callable[..., dict[str, Any]]
  domain: str = "general"

  def to_openrouter_schema(self) -> dict[str, Any]:
    return {
      "type": "function",
      "function": {
        "name": self.name,
        "description": self.description,
        "parameters": self.parameters,
      },
    }


class DomainToolkit:
  """Base container for a group of related domain tools."""

  def __init__(self, domain: str):
    self.domain = domain
    self._tools: dict[str, ToolDefinition] = {}

  def register(
    self,
    name: str,
    description: str,
    parameters: dict[str, Any],
    handler: Callable[..., dict[str, Any]],
  ) -> None:
    self._tools[name] = ToolDefinition(
      name=name,
      description=description,
      parameters=parameters,
      handler=handler,
      domain=self.domain,
    )

  def get_definitions(self) -> list[dict[str, Any]]:
    return [tool.to_openrouter_schema() for tool in self._tools.values()]

  def can_handle(self, name: str) -> bool:
    return name in self._tools

  def execute(self, name: str, args: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    if name not in self._tools:
      return {"error": f"unknown_tool:{name}"}
    return self._tools[name].handler(args, **kwargs)


class ToolRegistry:
  """Central registry dispatching tool calls across domain toolkits."""

  def __init__(self) -> None:
    self._toolkits: dict[str, DomainToolkit] = {}

  def register_toolkit(self, toolkit: DomainToolkit) -> None:
    self._toolkits[toolkit.domain] = toolkit

  def get_schemas_for_domains(self, domains: Optional[list[str]] = None) -> list[dict[str, Any]]:
    schemas: list[dict[str, Any]] = []
    target_toolkits = (
      [self._toolkits[d] for d in domains if d in self._toolkits]
      if domains
      else list(self._toolkits.values())
    )
    for tk in target_toolkits:
      schemas.extend(tk.get_definitions())
    return schemas

  def can_handle(self, name: str) -> bool:
    return any(tk.can_handle(name) for tk in self._toolkits.values())

  def execute(self, name: str, args: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    for tk in self._toolkits.values():
      if tk.can_handle(name):
        return tk.execute(name, args, **kwargs)
    return {"error": f"unknown_tool:{name}"}
