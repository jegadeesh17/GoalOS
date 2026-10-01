"""Goals & Horizon toolkit for active goal pacing and milestone retrieval."""

from __future__ import annotations

from typing import Any, Optional

from ai.tools.registry import DomainToolkit
from database.repositories.goal_repository import GoalRepository
from services.yearly_pacing_service import YearlyPacingService


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

  def get_goal_pacing_handler(args: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    horizon = args.get("horizon")
    if horizon not in (None, "1-year", "5-year", "10-year"):
      return {"error": f"horizon must be one of 1-year, 5-year, 10-year (got {horizon!r})"}
    r = kwargs.get("goal_repo") or repo
    goals = YearlyPacingService(goal_repo=r).evaluate_all(horizon=horizon)
    return {"goals": goals, "count": len(goals)}

  toolkit.register(
    name="get_active_goals",
    description="Return all currently active multi-horizon goals with title, category, horizon, and progress.",
    parameters={"type": "object", "properties": {}},
    handler=get_active_goals_handler,
  )

  toolkit.register(
    name="get_horizon_pacing",
    description="Get goals structured across 1-month, 1-year, 5-year, and 10-year life horizons with pacing details.",
    parameters={"type": "object", "properties": {}},
    handler=get_horizon_pacing_handler,
  )

  toolkit.register(
    name="get_goal_pacing",
    description=(
      "Measured pace of 1-year, 5-year and 10-year goals against their numeric targets and monthly check-ins. "
      "Each goal reports ahead/on_pace/behind with the latest value vs the expected value, or an honest status "
      "(qualitative, no_check_ins, baseline_only, no_deadline) when it cannot be measured."
    ),
    parameters={
      "type": "object",
      "properties": {
        "horizon": {
          "type": "string",
          "enum": ["1-year", "5-year", "10-year"],
          "description": "Limit to one horizon (default: all three)",
        },
      },
    },
    handler=get_goal_pacing_handler,
  )

  return toolkit
