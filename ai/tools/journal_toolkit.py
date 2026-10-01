"""Journal & Habits toolkit for daily log metrics, task completion, and execution consistency."""

from __future__ import annotations

from typing import Any, Optional

from ai.tools.registry import DomainToolkit
from database.repositories.log_repository import LogRepository
from services.monthly_analytics_service import MonthlyAnalyticsService
from services.weekly_sync_service import WeeklySyncService


def build_journal_toolkit(
  log_repo: Optional[LogRepository] = None,
  sync_service: Optional[WeeklySyncService] = None,
) -> DomainToolkit:
  toolkit = DomainToolkit(domain="journal")
  repo = log_repo or LogRepository()
  sync = sync_service or WeeklySyncService()

  def get_monthly_progress_handler(args: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    r = kwargs.get("log_repo") or repo
    s = kwargs.get("sync_service") or sync
    logs = r.get_recent(31)
    raw_logs = [l.model_dump(mode="json") for l in logs]
    progress = s.calculate_monthly_progress(raw_logs)
    return {
      "monthly_progress": progress,
    }

  def get_recent_logs_handler(args: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    r = kwargs.get("log_repo") or repo
    days = int(args.get("days", 7))
    logs = r.get_recent(days)
    return {
      "logs": [
        {
          "date": l.date.isoformat() if hasattr(l.date, "isoformat") else str(l.date),
          "top_priority": l.top_priority,
          "task_completion_rate": l.task_completion_rate,
          "deep_work_hours": l.deep_work_hours,
          "energy_level": l.energy_level,
          "mood_morning": l.mood_morning,
          "mood_evening": l.mood_evening,
          "one_win": l.one_win,
          "one_lesson": l.one_lesson,
        }
        for l in logs
      ],
      "count": len(logs),
    }

  def get_monthly_snapshots_handler(args: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    months = max(1, min(int(args.get("months", 6)), 12))
    digest = (kwargs.get("monthly_service") or MonthlyAnalyticsService()).history_digest(months)
    return {"months": digest, "count": len(digest)}

  toolkit.register(
    name="get_monthly_progress",
    description="Get current month's journal logging progress, completion rate, and goal alignment pacing.",
    parameters={"type": "object", "properties": {}},
    handler=get_monthly_progress_handler,
  )

  toolkit.register(
    name="get_recent_logs",
    description="Get recent daily execution logs including sleep, mood, top priority, deep work, and lessons.",
    parameters={
      "type": "object",
      "properties": {
        "days": {
          "type": "integer",
          "description": "Number of days of history to inspect (default: 7)",
        },
      },
    },
    handler=get_recent_logs_handler,
  )

  toolkit.register(
    name="get_monthly_snapshots",
    description=(
      "Saved month-by-month analytics, oldest first: task completion, sleep and schedule, scores, stuck tasks, "
      "statistically tested levers (with tier and n), next-month focus lines, and each month's goal state. "
      "Use it to compare months and judge the trend toward yearly goals."
    ),
    parameters={
      "type": "object",
      "properties": {
        "months": {
          "type": "integer",
          "description": "How many of the latest saved months to return (default 6, maximum 12)",
        },
      },
    },
    handler=get_monthly_snapshots_handler,
  )

  return toolkit
