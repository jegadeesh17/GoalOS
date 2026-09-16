"""Coordinator / Supervisor Agent for GoalOS multi-agent coaching workflows."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any, Optional

from ai.openrouter_client import OpenRouterClient
from database.repositories.coach_session_repository import CoachSessionRepository
from database.repositories.goal_repository import GoalRepository
from database.repositories.log_repository import LogRepository
from models.coach_session import CoachChatRequest, CoachChatResponse
from services.life_calendar_service import LifeCalendarService
from services.memory_service import MemoryService
from services.persona_service import PersonaService


class CoordinatorPipeline:
  """Supervisor orchestrator routing conversational intent to specialized domain tools and state."""

  def __init__(
    self,
    session_repo: Optional[CoachSessionRepository] = None,
    openrouter_client: Optional[OpenRouterClient] = None,
    memory_service: Optional[MemoryService] = None,
    goal_repo: Optional[GoalRepository] = None,
    log_repo: Optional[LogRepository] = None,
    calendar_service: Optional[LifeCalendarService] = None,
    persona_service: Optional[PersonaService] = None,
  ) -> None:
    self.session_repo = session_repo or CoachSessionRepository()
    self.client = openrouter_client or OpenRouterClient()
    self.memory_service = memory_service or MemoryService()
    self.goal_repo = goal_repo or GoalRepository()
    self.log_repo = log_repo or LogRepository()
    self.calendar_service = calendar_service or LifeCalendarService()
    self.persona_service = persona_service or PersonaService()

  def classify_intent(self, message: str, preferred_domain: Optional[str] = None) -> tuple[str, list[str]]:
    """Determine domain intent and relevant tool namespaces."""
    if preferred_domain and preferred_domain in ("execution", "goals", "memory", "calendar", "general"):
      if preferred_domain == "execution":
        return "execution_coaching", ["journal", "goals"]
      if preferred_domain == "goals":
        return "goals_pacing", ["goals", "memory"]
      if preferred_domain == "memory":
        return "memory_retrieval", ["memory"]
      if preferred_domain == "calendar":
        return "lifespan_awareness", ["calendar", "goals"]
      return "general_coaching", ["memory", "goals", "journal", "calendar"]

    msg_lower = message.lower()
    if any(k in msg_lower for k in ("morning", "evening", "today", "task", "habit", "sleep", "distraction", "routine")):
      return "execution_coaching", ["journal", "goals", "memory"]
    if any(k in msg_lower for k in ("goal", "horizon", "milestone", "pacing", "sprint", "quarter", "vision")):
      return "goals_pacing", ["goals", "journal", "memory"]
    if any(k in msg_lower for k in ("remember", "lesson", "past", "history", "insight", "commitment", "rule")):
      return "memory_retrieval", ["memory", "goals"]
    if any(k in msg_lower for k in ("life", "weeks", "year", "age", "calendar", "memento mori", "long term")):
      return "lifespan_awareness", ["calendar", "goals"]

    return "general_coaching", ["memory", "goals", "journal", "calendar"]

  def chat(self, request: CoachChatRequest) -> CoachChatResponse:
    """Run full supervisor coordination loop for a user query."""
    start_time = time.time()
    trace_id = f"tr_{uuid.uuid4().hex[:12]}"

    # 1. Resolve or create session
    session = None
    if request.session_id:
      session = self.session_repo.get_session(request.session_id)
    if not session:
      session = self.session_repo.create_session(
        title=f"Coaching: {request.message[:40]}..." if len(request.message) > 40 else request.message,
        session_id=request.session_id,
      )

    session_id = session.id
    blackboard = dict(session.blackboard or {})

    # 2. Persist user message
    self.session_repo.append_message(
      session_id=session_id,
      role="user",
      content=request.message,
    )

    # 3. Classify intent & target toolkits
    intent, target_domains = self.classify_intent(request.message, request.preferred_domain)

    # 4. Check remote AI consent and API key availability
    has_key = bool(self.client.api_key and self.client.api_key.strip())
    if not request.remote_ai_consent or not has_key:
      fallback_resp = self._run_deterministic_fallback(
        message=request.message,
        intent=intent,
        session_id=session_id,
        blackboard=blackboard,
        trace_id=trace_id,
        reason="remote_ai_disabled" if not request.remote_ai_consent else "no_api_key",
      )
      fallback_resp.latency_ms = round((time.time() - start_time) * 1000, 2)
      return fallback_resp

    # 5. Direct Context Grounding: retrieve domain data upfront
    context_blocks: list[str] = []
    tools_used: list[str] = []

    if "goals" in target_domains:
      try:
        goals = self.goal_repo.get_active()
        if goals:
          tools_used.append("get_active_goals")
          goals_summary = "\n".join(
            f"- [{g.horizon}] {g.title} (Progress: {g.progress}%, Category: {g.category})"
            for g in goals[:8]
          )
          context_blocks.append(f"ACTIVE GOALS:\n{goals_summary}")
      except Exception:
        pass

    if "journal" in target_domains:
      try:
        recent_logs = self.log_repo.get_recent(3)
        if recent_logs:
          tools_used.append("get_recent_logs")
          logs_summary = "\n".join(
            f"- {l.date}: Top Priority: {l.top_priority or 'None'}, Reflection: {(l.journal_entry or '')[:120]}"
            for l in recent_logs if l
          )
          context_blocks.append(f"RECENT DAILY EXECUTION:\n{logs_summary}")
      except Exception:
        pass

    if "memory" in target_domains:
      try:
        memories = self.memory_service.repo.search_text(request.message, 4)
        if not memories:
          memories = self.memory_service.repo.get_all(status="active")[:4]
        if memories:
          tools_used.append("search_memories")
          mems_summary = "\n".join(
            f"- [{m.type}] {m.text[:140]}" for m in memories
          )
          context_blocks.append(f"RELEVANT COGNITIVE MEMORIES:\n{mems_summary}")
      except Exception:
        pass

    if "calendar" in target_domains:
      try:
        cal = self.calendar_service.get_summary()
        tools_used.append("get_lifespan_stats")
        context_blocks.append(
          f"LIFE CALENDAR STATS:\n- Weeks Lived: {cal.weeks_lived} / {cal.total_weeks} ({cal.percentage_lived}% elapsed)\n- Weeks Remaining: {cal.weeks_remaining}"
        )
      except Exception:
        pass

    grounded_context = "\n\n".join(context_blocks)

    # 6. Build supervisor prompt with history, blackboard, and grounded data
    system_prompt = self._build_system_prompt(intent, blackboard, session.messages, grounded_context)
    user_prompt = f"User Request: {request.message}"

    try:
      ai_result = self.client.complete(
        system_prompt=system_prompt,
        user_message=user_prompt,
        temperature=0.5,
        max_tokens=800,
        trace_id=trace_id,
        session_id=session_id,
        span_name=f"coordinator_{intent}",
      )

      if isinstance(ai_result, dict) and ai_result.get("error"):
        fallback_resp = self._run_deterministic_fallback(
          message=request.message,
          intent=intent,
          session_id=session_id,
          blackboard=blackboard,
          trace_id=trace_id,
          reason=f"openrouter_error:{ai_result.get('error')}",
        )
        fallback_resp.latency_ms = round((time.time() - start_time) * 1000, 2)
        return fallback_resp

      reply_text = str(ai_result).strip()
      if reply_text.startswith("Error:"):
        fallback_resp = self._run_deterministic_fallback(
          message=request.message,
          intent=intent,
          session_id=session_id,
          blackboard=blackboard,
          trace_id=trace_id,
          reason=f"openrouter_error:{reply_text[:60]}",
        )
        fallback_resp.latency_ms = round((time.time() - start_time) * 1000, 2)
        return fallback_resp

      # Update blackboard with intent and latest activity
      blackboard["last_intent"] = intent
      blackboard["last_active_at"] = time.time()
      self.session_repo.update_blackboard(session_id, blackboard)

      # Persist assistant response
      self.session_repo.append_message(
        session_id=session_id,
        role="assistant",
        content=reply_text,
        agent_name="CoordinatorAgent",
        tool_calls=[{"tool": t} for t in tools_used],
      )

      latency_ms = round((time.time() - start_time) * 1000, 2)
      return CoachChatResponse(
        session_id=session_id,
        reply=reply_text,
        agent_name="CoordinatorAgent",
        intent=intent,
        confidence=0.92,
        source="ai_agent",
        tools_used=tools_used,
        blackboard=blackboard,
        trace_id=trace_id,
        latency_ms=latency_ms,
      )

    except Exception as exc:
      fallback_resp = self._run_deterministic_fallback(
        message=request.message,
        intent=intent,
        session_id=session_id,
        blackboard=blackboard,
        trace_id=trace_id,
        reason=f"exception:{str(exc)}",
      )
      fallback_resp.latency_ms = round((time.time() - start_time) * 1000, 2)
      return fallback_resp

  def _build_system_prompt(
    self,
    intent: str,
    blackboard: dict[str, Any],
    history: list[Any],
    grounded_context: str = "",
  ) -> str:
    recent_history_text = "\n".join(
      f"- {m.role.upper()}: {m.content}" for m in history[-6:]
    ) if history else "No previous dialog in this session."

    bb_text = json.dumps(blackboard, default=str)
    context_section = f"\nREAL-TIME GROUNDED USER DATA:\n{grounded_context}\n" if grounded_context else ""

    try:
      persona_section = self.persona_service.build_directives()
    except Exception:
      # Persona is a preference layer; never let it block a coaching turn.
      persona_section = ""

    return f"""You are the GoalOS Executive AI Coordinator.
You supervise multi-horizon goal pacing, morning/evening daily execution, cognitive memory retrieval, and 70-year lifespan awareness.

CURRENT INTENT: {intent.upper()}
SHARED SESSION BLACKBOARD: {bb_text}
{context_section}{persona_section}
RECENT CONVERSATION HISTORY:
{recent_history_text}

OPERATING PRINCIPLES:
1. Grounding & Anti-Hallucination: Ground your coaching directly in the real-time user data provided above.
2. Direct & Actionable: Give concise, high-density executive coaching. Avoid fluffy generic filler or excessive disclaimers.
3. Multi-Horizon Pacing: Connect daily execution to 1-month sprints, 1-year horizons, and 5-year visions.
4. If the user asks what to focus on, refer explicitly to their active priorities and goals.
"""

  def _run_deterministic_fallback(
    self,
    message: str,
    intent: str,
    session_id: str,
    blackboard: dict[str, Any],
    trace_id: str,
    reason: str,
  ) -> CoachChatResponse:
    """Generate high-utility local rule-based coaching when remote AI is unavailable."""
    active_goals = self.goal_repo.get_active()
    recent_logs = self.log_repo.get_recent(7)
    lifespan = self.calendar_service.get_summary()

    goal_titles = [g.title for g in active_goals[:3]]
    goals_summary = f"Active Goals ({len(active_goals)}): " + (", ".join(goal_titles) if goal_titles else "None set yet.")

    avg_completion = (
      sum(l.task_completion_rate or 0.0 for l in recent_logs) / len(recent_logs)
      if recent_logs
      else 0.0
    )

    reply_lines = [
      "**[GoalOS Local Executive Rule Engine]**",
      f"• **Intent:** {intent.replace('_', ' ').title()}",
      f"• **Lifespan Awareness:** {lifespan['weeks_lived']}/{lifespan['total_weeks']} weeks lived ({round(lifespan['percentage_lived'], 1)}%). {lifespan['weeks_remaining']} weeks remaining.",
      f"• **7-Day Task Completion:** {round(avg_completion, 1)}%",
      f"• **Current Trajectory:** {goals_summary}",
      "",
      "**Recommended Executive Action:**",
      "1. Lock in your core 90-minute deep work block for your #1 priority task before noon.",
      "2. Protect focus windows from micro-distractions and context switching.",
      "3. Align today's tasks directly with your active monthly milestone.",
    ]
    reply = "\n".join(reply_lines)

    blackboard["last_fallback_reason"] = reason
    self.session_repo.update_blackboard(session_id, blackboard)

    self.session_repo.append_message(
      session_id=session_id,
      role="assistant",
      content=reply,
      agent_name="DeterministicRuleEngine",
    )

    return CoachChatResponse(
      session_id=session_id,
      reply=reply,
      agent_name="DeterministicRuleEngine",
      intent=intent,
      confidence=0.75,
      source="deterministic_rules",
      tools_used=[],
      blackboard=blackboard,
      trace_id=trace_id,
      fallback_reason=reason,
    )
