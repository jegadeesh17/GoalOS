"""Central coach orchestration service."""

import json
import logging
from datetime import date, timedelta

from ai.openrouter_client import OpenRouterClient
from ai.pipelines.agent_morning_coach import run_agent_morning_coach
from ai.pipelines.evening_coach import run_evening_coach
from ai.pipelines.future_self_coach import run_future_self_coach
from ai.pipelines.goal_alignment_coach import run_goal_alignment_coach
from ai.pipelines.morning_coach import run_morning_coach
from ai.pipelines.reflection_coach import run_reflection_coach
from ai.pipelines.weekly_coach import run_weekly_coach
from database.connection import get_db
from database.repositories.coach_repository import CoachRepository
from database.repositories.goal_repository import GoalRepository
from database.repositories.log_repository import LogRepository
from database.repositories.score_repository import ScoreRepository
from database.repositories.weekly_review_repository import WeeklyReviewRepository
from models.coach_output import CoachingEvidence, MorningCoachOutput
from models.coach_response import CoachResponseCreate
from models.daily_log import DailyLog, DailyLogUpdate
from models.weekly_review import WeeklyReviewCreate
from services.analytics_service import calculate_daily_scores
from services.memory_service import MemoryService
from services.mentor_briefing import build_mentor_briefing
from services.settings_service import SettingsService

logger = logging.getLogger(__name__)


class CoachService:
  """Orchestrates analytics, memory, and AI coaching."""

  def __init__(self):
    self.goal_repo = GoalRepository()
    self.log_repo = LogRepository()
    self.score_repo = ScoreRepository()
    self.coach_repo = CoachRepository()
    self.weekly_repo = WeeklyReviewRepository()
    self.memory_service = MemoryService()
    self.llm = OpenRouterClient()
    self.settings_service = SettingsService()

  def _get_user_vision(self) -> dict:
    with get_db() as conn:
      row = conn.execute("SELECT * FROM user WHERE id = 1").fetchone()
    if row:
      d = dict(row)
      return {
        "one_year_vision": d.get("one_year_vision") or "",
        "five_year_vision": d.get("five_year_vision") or "",
        "ten_year_vision": d.get("life_vision") or "",
      }
    return {}

  def _serialize_log(self, log: DailyLog) -> dict:
    return log.model_dump(mode="json")

  def _serialize_goal(self, goal) -> dict:
    return goal.model_dump(mode="json")

  def _refresh_llm(self) -> None:
    """Always pick up latest .env model/key before AI calls."""
    self.llm.refresh_config()

  def _remote_ai_allowed(self) -> bool:
    return bool(self.settings_service.remote_ai_allowed() and self.llm.api_key)

  def _with_evidence(self, result: dict, context: dict) -> dict:
    """Validate public output and attach bounded, non-journal evidence references."""
    evidence: list[CoachingEvidence] = []
    for goal in context.get("active_goals", [])[:3]:
      evidence.append(CoachingEvidence(goal_id=goal.get("id"), goal_title=goal.get("title")))
    for memory in context.get("relevant_memories", [])[:3]:
      evidence.append(CoachingEvidence(memory_id=memory.get("id"), source_date=memory.get("source_date")))
    result["evidence"] = [item.model_dump(mode="json") for item in evidence]
    try:
      return MorningCoachOutput.model_validate(result).model_dump(mode="json")
    except Exception as exc:
      logger.warning("coach_output_invalid event=morning reason=%s", type(exc).__name__)
      from ai.pipelines._base import fallback_morning
      fallback = fallback_morning(context)
      fallback.update({"fallback_reason": "invalid_response", "fallback_detail": "The model response did not match the coach schema", "evidence": result["evidence"]})
      return MorningCoachOutput.model_validate(fallback).model_dump(mode="json")

  def build_context(self, target_date: date, query: str = "") -> dict:
    """Assemble full context for AI calls."""
    goals = self.goal_repo.get_active()
    recent_logs = self.log_repo.get_recent(14)
    scores = self.score_repo.get_by_date(target_date)
    weekly = None
    with get_db() as conn:
      row = conn.execute(
        "SELECT * FROM weekly_reviews ORDER BY week_start DESC LIMIT 1"
      ).fetchone()
      if row:
        weekly = dict(row)

    recent_coach = [
      r.model_dump(mode="json") for r in self.coach_repo.get_recent(5)
    ]

    ctx = {
      "date": target_date.isoformat(),
      "user_vision": self._get_user_vision(),
      "active_goals": [self._serialize_goal(g) for g in goals],
      "recent_logs": [self._serialize_log(l) for l in recent_logs],
      "current_scores": scores.model_dump(mode="json") if scores else {},
      "recent_weekly_review": weekly,
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

  def get_morning_coaching(self, target_date: date, log: DailyLog) -> dict:
    """Run mentor pipeline and store output."""
    self._refresh_llm()
    context = self.build_context(target_date, log.planned_tasks or log.gratitude or "")
    context["today_log"] = self._serialize_log(log)
    context["mentor_briefing"] = build_mentor_briefing(
      target_date,
      context["today_log"],
      self.log_repo.get_recent(14),
      context["user_vision"],
      context["recent_coach_advice"],
    )
    if self._remote_ai_allowed():
      result = run_agent_morning_coach(context, self.llm)
      if not (isinstance(result, dict) and result.get("mentor_rule")):
        result = run_morning_coach(context, self.llm)
    else:
      from ai.pipelines._base import fallback_morning
      result = fallback_morning(context)
      result["fallback_reason"] = "remote_ai_consent_required" if self.llm.api_key else "no_api_key"
      result["fallback_detail"] = "Enable remote AI consent in Settings to send journal context to OpenRouter."
    result = self._with_evidence(result, context)
    logger.info("coach_complete event=morning source=%s retrieval_count=%d fallback=%s", result["source"], len(context["relevant_memories"]), result.get("fallback_reason"))

    self.log_repo.update(log.id, DailyLogUpdate(
      morning_ai_output=json.dumps(result),
      morning_completed=True,
    ))
    self.coach_repo.create(CoachResponseCreate(
      session_type="morning",
      ai_response=json.dumps(result),
      date=target_date,
    ))
    return result

  def get_evening_coaching(self, target_date: date, log: DailyLog) -> dict:
    """Run evening pipeline, extract memories, calculate scores."""
    self._refresh_llm()
    context = self.build_context(target_date, log.journal_entry or "")
    context["today_log"] = self._serialize_log(log)
    if self._remote_ai_allowed():
      result = run_evening_coach(context, self.llm)
    else:
      from ai.pipelines._base import fallback_evening
      result = fallback_evening(context)
      result["fallback_reason"] = "remote_ai_consent_required" if self.llm.api_key else "no_api_key"

    for mem in result.get("memories_to_store", []):
      self.memory_service.store(
        mem.get("text", ""),
        mem.get("type", "journal_insight"),
        mem.get("importance", 0.6),
        target_date,
        "evening",
        log.id,
      )

    if result.get("commitment_extracted"):
      self.memory_service.store(
        result["commitment_extracted"], "commitment", 0.7, target_date, "evening", log.id
      )

    logs_30d = self.log_repo.get_range(target_date - timedelta(days=30), target_date)
    goals = self.goal_repo.get_active()
    recent_scores = self.score_repo.get_recent(7)
    scores_7d = [s.overall_growth_score or 50 for s in recent_scores]
    calculate_daily_scores(log, goals, logs_30d, scores_7d)

    self.log_repo.update(log.id, DailyLogUpdate(
      evening_ai_output=json.dumps(result),
      evening_completed=True,
    ))
    self.coach_repo.create(CoachResponseCreate(
      session_type="evening",
      ai_response=json.dumps(result),
      date=target_date,
    ))
    return result

  def get_weekly_coaching(self, week_start: date) -> dict:
    """Run weekly pipeline and store in weekly_reviews."""
    self._refresh_llm()
    from services.journal_helpers import week_task_stats

    week_end = week_start + timedelta(days=6)
    week_logs = self.log_repo.get_range(week_start, week_end)
    context = self.build_context(week_end)
    context["week_logs"] = [self._serialize_log(l) for l in week_logs]
    context["week_task_stats"] = week_task_stats(week_logs)
    if self._remote_ai_allowed():
      result = run_weekly_coach(context, self.llm)
    else:
      from ai.pipelines._base import fallback_weekly
      result = fallback_weekly(context)
      result["fallback_reason"] = "remote_ai_consent_required" if self.llm.api_key else "no_api_key"

    self.weekly_repo.upsert(WeeklyReviewCreate(
      week_start=week_start,
      week_end=week_end,
      ai_output=json.dumps(result),
    ))
    self.coach_repo.create(CoachResponseCreate(
      session_type="weekly",
      ai_response=json.dumps(result),
      date=week_start,
    ))
    return result

  def get_goal_alignment(self) -> dict:
    self._refresh_llm()
    context = self.build_context(date.today())
    if self._remote_ai_allowed():
      return run_goal_alignment_coach(context, self.llm)
    from ai.pipelines._base import fallback_goal_alignment
    return fallback_goal_alignment(context)

  def prefill_from_journal(self, journal_text: str) -> dict:
    """AI pre-fill win and lesson from journal."""
    self._refresh_llm()
    context = self.build_context(date.today())
    if self._remote_ai_allowed():
      result = run_reflection_coach(context, journal_text, self.llm)
    else:
      from ai.pipelines._base import fallback_reflection
      result = fallback_reflection(context)
    return {
      "one_win": result.get("insights", [""])[0] if result.get("insights") else "",
      "one_lesson": result.get("patterns", [""])[0] if result.get("patterns") else "",
    }

  def chat(self, message: str, history: list[dict]) -> dict:
    """Conversational coach with full context."""
    self._refresh_llm()
    context = self.build_context(date.today(), message)
    system = (
      "You are the Mentor — a strict personal guide shaping the user into who they want to become. "
      "Answer based on their journals, goals, and patterns. Be direct. Issue rules, not suggestions. "
      "1-year, 5-year, and 10-year goals have equal priority — daily work must advance all three."
    )
    history_text = "\n".join(f"{m['role']}: {m['content']}" for m in history[-10:])
    user_msg = f"Context:\n{json.dumps(context, default=str, indent=2)}\n\nHistory:\n{history_text}\n\nUser: {message}"

    try:
      if not self._remote_ai_allowed():
        raise RuntimeError("remote_ai_consent_required")
      response = self.llm.complete(system, user_msg, temperature=0.7)
      if isinstance(response, str):
        ai_text = response
      else:
        ai_text = response.get("message", str(response))
    except Exception as e:
      logger.error("Chat failed: %s", e)
      ai_text = "I'm having trouble connecting right now. Please try again."

    if any(kw in message.lower() for kw in ("i will", "i'll", "tomorrow i")):
      self.memory_service.store(message, "commitment", 0.7, date.today(), "chat")

    self.coach_repo.create(CoachResponseCreate(
      session_type="chat",
      user_message=message,
      ai_response=ai_text,
      date=date.today(),
    ))
    return {
      "response": ai_text,
      "memories_used": context.get("relevant_memories", [])[:3],
      "goals_referenced": [g.get("title") for g in context.get("active_goals", [])[:3]],
      "commitments": context.get("unfulfilled_commitments", [])[:3],
    }

  def get_future_self(self) -> dict:
    self._refresh_llm()
    context = self.build_context(date.today())
    if self._remote_ai_allowed():
      return run_future_self_coach(context, self.llm)
    from ai.pipelines._base import fallback_future_self
    return fallback_future_self(context)

  def get_dashboard_recommendation(self) -> str:
    """Today's mentor rule for dashboard."""
    self._refresh_llm()
    today = date.today()
    log = self.log_repo.get_by_date(today)
    if log and log.morning_ai_output:
      try:
        output = json.loads(log.morning_ai_output)
        if output.get("mentor_rule"):
          return output["mentor_rule"]
      except json.JSONDecodeError:
        pass
    context = self.build_context(today)
    if not self._remote_ai_allowed():
      from ai.pipelines._base import fallback_morning
      result = fallback_morning(context)
    else:
      result = run_morning_coach(context, self.llm)
    return result.get("mentor_rule", "Complete your morning journal to receive today's rule.")

  def get_dashboard_interpretations(self, metrics: dict) -> dict:
    """Batch interpretations for dashboard metrics."""
    self._refresh_llm()
    system = "Generate one short interpretation sentence per metric. Return JSON with metric keys."
    user_msg = f"Metrics: {json.dumps(metrics)}\nReturn JSON like {{'streak': '...', 'growth': '...'}}"
    try:
      if not self._remote_ai_allowed():
        raise RuntimeError("remote_ai_consent_required")
      result = self.llm.complete(system, user_msg, response_format={"type": "json_object"}, temperature=0.5)
      if isinstance(result, dict) and "error" not in result:
        return result
    except Exception:
      pass
    return {k: f"Your {k} reflects your recent activity." for k in metrics}
