"""Central coach orchestration service."""

import json
from datetime import date
from typing import Optional

from ai.openrouter_client import OpenRouterClient
from ai.pipelines.future_self_coach import run_future_self_coach
from ai.pipelines.progress_coach import run_progress_coach
from database.connection import get_db
from database.repositories.coach_repository import CoachRepository
from database.repositories.goal_repository import GoalRepository
from database.repositories.log_repository import LogRepository
from database.repositories.score_repository import ScoreRepository
from models.coach_response import CoachResponseCreate
from models.daily_log import DailyLog
from services.memory_service import MemoryService
from services.mentor_briefing import build_mentor_briefing
from services.pattern_service import PatternService
from services.settings_service import SettingsService


class CoachService:
  """Orchestrates analytics, memory, and AI coaching."""

  def __init__(self):
    self.goal_repo = GoalRepository()
    self.log_repo = LogRepository()
    self.score_repo = ScoreRepository()
    self.coach_repo = CoachRepository()
    self.memory_service = MemoryService()
    self.llm = OpenRouterClient()
    self.settings_service = SettingsService()

  def _get_user_vision(self) -> dict:
    """Derive the user's vision narrative from their active Goal records.

    Goals are the single source of truth for 1/5/10-year vision (no separate
    free-text fields) - each horizon's goal titles/reasons are joined into a
    short narrative for the AI coaching prompts.
    """
    categorized = self.goal_repo.get_by_horizons()

    def narrative(goals: list) -> str:
      parts = []
      for goal in goals:
        text = goal.title.strip()
        if goal.reason:
          text += f" ({goal.reason.strip()})"
        parts.append(text)
      return "; ".join(parts)

    return {
      "one_year_vision": narrative(categorized.get("1-year", [])),
      "five_year_vision": narrative(categorized.get("5-year", [])),
      "ten_year_vision": narrative(categorized.get("10-year", [])),
    }

  def _serialize_log(self, log: DailyLog) -> dict:
    return log.model_dump(mode="json")

  def _serialize_goal(self, goal) -> dict:
    return goal.model_dump(mode="json")

  def _refresh_llm(self) -> None:
    """Always pick up latest .env model/key before AI calls."""
    self.llm.refresh_config()

  def _remote_ai_allowed(self) -> bool:
    return bool(self.settings_service.remote_ai_allowed() and self.llm.api_key)

  def _get_current_age(self) -> Optional[float]:
    with get_db() as conn:
      row = conn.execute("SELECT birth_date FROM user WHERE id = 1").fetchone()
    if not row or not row["birth_date"]:
      return None
    birth = date.fromisoformat(row["birth_date"])
    return (date.today() - birth).days / 365.25

  def build_context(self, target_date: date, query: str = "") -> dict:
    """Assemble full context for AI calls."""
    goals = self.goal_repo.get_active()
    recent_logs = self.log_repo.get_recent(14)
    scores = self.score_repo.get_by_date(target_date)

    recent_coach = [
      r.model_dump(mode="json") for r in self.coach_repo.get_recent(5)
    ]

    # Construct a clean narrative digest of recent text reflections (noise-free)
    journal_digest = []
    for l in recent_logs:
      if not l:
        continue
      entry_text = (l.journal_entry or "").strip()
      takeaway_text = (l.takeaway or l.one_lesson or "").strip()
      gratitude_text = (l.gratitude or "").strip()
      tasks_text = (l.planned_tasks or l.tasks_completed or "").strip()
      
      if entry_text or takeaway_text or gratitude_text or tasks_text:
        journal_digest.append({
          "date": l.date.isoformat(),
          "reflection": entry_text,
          "takeaway": takeaway_text,
          "gratitude": gratitude_text,
          "tasks": tasks_text,
          "task_completion_rate": l.task_completion_rate,
        })

    # Extract multi-day behavioral patterns
    pattern_report = PatternService().analyze_patterns(recent_logs, goals, target_date=target_date)

    current_age = self._get_current_age()
    # None when birth_date is unset - never guess an age.
    age_in_10_years = round(current_age) + 10 if current_age is not None else None

    ctx = {
      "date": target_date.isoformat(),
      "user_vision": self._get_user_vision(),
      "current_age_in_10_years": age_in_10_years,
      "active_goals": [self._serialize_goal(g) for g in goals],
      "journal_text_digest": journal_digest,
      "recent_logs": [self._serialize_log(l) for l in recent_logs],
      "current_scores": scores.model_dump(mode="json") if scores else {},
      "pattern_analysis": pattern_report,
      "relevant_memories": [
        m.model_dump(mode="json") for m in self.memory_service.retrieve(query or "mistakes patterns lessons", 8)
      ],
      "unfulfilled_commitments": [
        m.model_dump(mode="json") for m in self.memory_service.get_commitments()
      ],
      "recent_coach_advice": recent_coach,
    }
    ctx["mentor_briefing"] = build_mentor_briefing(
      target_date,
      ctx.get("today_log"),
      recent_logs,
      ctx["user_vision"],
      recent_coach,
    )
    return ctx

  def get_progress_coaching(self, target_date: date = None) -> dict:
    import calendar

    from services.weekly_sync_service import WeeklySyncService

    self._refresh_llm()
    if not target_date:
      target_date = date.today()

    month_start = target_date.replace(day=1)
    days_in_month = calendar.monthrange(target_date.year, target_date.month)[1]
    month_end = target_date.replace(day=days_in_month)
    month_name = month_start.strftime("%B %Y")

    month_logs_objs = self.log_repo.get_range(month_start, month_end)
    month_logs = [self._serialize_log(l) for l in month_logs_objs]

    context = self.build_context(target_date, f"monthly progress goals alignment for {month_name}")

    sync = WeeklySyncService()
    active_goals = self.goal_repo.get_active()
    monthly_progress = sync.calculate_monthly_progress(
      month_logs,
      month_start=month_start,
      month_name=month_name,
      active_goals=active_goals,
    )

    # Pass past logs (e.g. previous month) as historical baseline context for coaching insights
    prev_logs_objs = self.log_repo.get_recent(31)
    context["historical_baseline_logs"] = [self._serialize_log(l) for l in prev_logs_objs if l.date < month_start]

    context["monthly_progress"] = monthly_progress
    context["month_name"] = month_name
    context["target_date"] = target_date.isoformat()

    if self._remote_ai_allowed():
      result = run_progress_coach(context, self.llm)
    else:
      from ai.pipelines._base import fallback_progress
      result = fallback_progress(context)
      result["fallback_reason"] = "remote_ai_consent_required" if self.llm.api_key else "no_api_key"

    self.coach_repo.create(
      CoachResponseCreate(
        session_type="progress",
        ai_response=json.dumps(result),
        date=target_date,
      )
    )
    return result

  def get_future_self_coaching(self, target_date: date | None = None) -> dict:
    self._refresh_llm()
    context = self.build_context(target_date or date.today())
    if self._remote_ai_allowed():
      return run_future_self_coach(context, self.llm)
    from ai.pipelines._base import fallback_future_self
    return fallback_future_self(context)
