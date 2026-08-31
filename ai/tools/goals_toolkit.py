"""Goals & Horizon toolkit for active goal pacing and milestone retrieval."""

from __future__ import annotations

from typing import Any, Optional

from ai.tools.registry import DomainToolkit
from database.repositories.goal_repository import GoalRepository


def build_goals_toolkit(goal_repo: Optional[GoalRepository] = None) -> DomainToolkit:
  toolkit = DomainToolkit(domain="goals")
  repo = goal_repo or GoalRepository()

  def get_active_goals_handler(args: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    r = kwargs.get("goal_repo") or repo
    goals = r.get_active()
    return {
      "goals": [
        {
          "id": g.id,
          "title": g.title,
          "category": g.category,
          "horizon": g.horizon,
          "priority": g.priority,
          "progress": g.progress,
          "status": g.status,
        }
        for g in goals
      ],
      "count": len(goals),
    }

  def get_horizon_pacing_handler(args: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    r = kwargs.get("goal_repo") or repo
    grouped = r.get_by_horizons()
    pacing_summary = {
      horizon: [
        {"id": g.id, "title": g.title, "progress": g.progress, "priority": g.priority}
        for g in goal_list
      ]
      for horizon, goal_list in grouped.items()
    }
    return {
      "horizons": pacing_summary,
      "total_active": sum(len(gl) for gl in grouped.values()),
    }

  toolkit.register(
    name="get_active_goals",
    description="Return all currently active multi-horizon goals with title, category, horizon, and progress.",
    parameters={"type": "object", "properties": {}},
    handler=get_active_goals_handler,
  )

  toolkit.register(
    name="get_horizon_pacing",
    description="Get goals structured across 1-month, 1-year, and 5-year life horizons with pacing details.",
    parameters={"type": "object", "properties": {}},
    handler=get_horizon_pacing_handler,
  )

  return toolkit
