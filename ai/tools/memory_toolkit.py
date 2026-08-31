"""Cognitive Memory toolkit for semantic and lexical memory retrieval."""

from __future__ import annotations

from typing import Any, Optional

from ai.tools.registry import DomainToolkit
from services.memory_service import MemoryService


def build_memory_toolkit(memory_service: Optional[MemoryService] = None) -> DomainToolkit:
  toolkit = DomainToolkit(domain="memory")
  mem_svc = memory_service or MemoryService()

  def search_memories_handler(args: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    svc = kwargs.get("memory_service") or mem_svc
    query = str(args.get("query", "")).strip()
    if not query:
      return {"memories": [], "count": 0}
    top_k = int(args.get("top_k", 5))
    memories = svc.retrieve(query, top_k=top_k)
    return {
      "memories": [
        {
          "id": m.id,
          "text": m.text,
          "type": m.type,
          "importance": m.importance,
          "source_date": m.source_date.isoformat() if m.source_date else None,
        }
        for m in memories
      ],
      "count": len(memories),
    }

  toolkit.register(
    name="search_memories",
    description=(
      "Search past journal insights, lessons, and commitments using 5-factor hybrid RAG. "
      "Use when you need relevant user history, past habits, or previous mistakes."
    ),
    parameters={
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "Natural-language search query (e.g. 'gym consistency', 'deep work focus')",
        },
        "top_k": {
          "type": "integer",
          "description": "Maximum number of relevant memories to retrieve (default: 5)",
        },
      },
      "required": ["query"],
    },
    handler=search_memories_handler,
  )

  return toolkit
