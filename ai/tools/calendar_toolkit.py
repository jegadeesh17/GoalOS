"""Life Calendar toolkit for Memento Mori lifespan perspective and decade statistics."""

from __future__ import annotations

from typing import Any, Optional

from ai.tools.registry import DomainToolkit
from services.life_calendar_service import LifeCalendarService


def build_calendar_toolkit(calendar_service: Optional[LifeCalendarService] = None) -> DomainToolkit:
  toolkit = DomainToolkit(domain="calendar")
  cal_svc = calendar_service or LifeCalendarService()

  def get_lifespan_stats_handler(args: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    svc = kwargs.get("calendar_service") or cal_svc
    summary = svc.get_summary()
    return {
      "target_age": summary["target_age"],
      "total_weeks": summary["total_weeks"],
      "weeks_lived": summary["weeks_lived"],
      "weeks_remaining": summary["weeks_remaining"],
      "percentage_lived": summary["percentage_lived"],
      "current_age_years": summary["age_years"],
    }

  toolkit.register(
    name="get_lifespan_stats",
    description="Get 70-year Memento Mori lifespan awareness statistics: weeks lived, weeks remaining, and percentage lived.",
    parameters={"type": "object", "properties": {}},
    handler=get_lifespan_stats_handler,
  )

  return toolkit
