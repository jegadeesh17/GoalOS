"""GoalOS FastAPI surface with CORS, REST CRUD for all domains, and coaching pipelines."""

from __future__ import annotations

import hmac
import logging
import os
import sys
from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi import Path as PathParam
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
  sys.path.insert(0, ROOT)

from ai.pipelines.coordinator import CoordinatorPipeline
from config.settings import settings
from database.connection import get_db
from database.migrations import run_migrations
from database.repositories.coach_session_repository import CoachSessionRepository
from database.repositories.goal_repository import GoalRepository
from database.repositories.log_repository import LogRepository
from database.repositories.memory_repository import MemoryRepository
from database.repositories.milestone_repository import MilestoneRepository
from database.repositories.monthly_repository import MonthlyRepository
from database.repositories.score_repository import ScoreRepository
from models.coach_session import (
  CoachChatRequest,
  CoachChatResponse,
  CoachSessionCreate,
  CoachSessionRead,
  TelemetrySpan,
  TelemetrySummaryResponse,
)
from models.daily_log import DailyLog, DailyLogUpdate
from models.goal import GoalCreate, GoalUpdate
from models.milestone import MilestoneCreate, MilestoneUpdate
from models.monthly import GoalMeasurementCreate, GoalPacePointCreate
from models.task_link import TaskLinkWrite
from services.coach_service import CoachService
from services.data_portability_service import DataPortabilityService
from services.life_calendar_service import LifeCalendarService
from services.memory_service import MemoryService
from services.monthly_analytics_service import MonthlyAnalyticsService
from services.observability_service import ObservabilityService
from services.pattern_service import PatternService
from services.report_service import ReportService
from services.settings_service import SettingsService
from services.task_link_service import TaskLinkService
from services.yearly_pacing_service import YearlyPacingService

logger = logging.getLogger(__name__)
MAX_REQUEST_BYTES = 512 * 1024
MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"

app = FastAPI(
  title="GoalOS Operating System API",
  version="2.1.0",
  description="Local-first API for GoalOS life calendar, journaling, goals, cognitive memory, and AI coaching.",
)

# Enable CORS for frontend development
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

api_router = APIRouter()


# ---------------------------------------------------------------------------
# Request & Response Schemas
# ---------------------------------------------------------------------------


class MemoryStoreRequest(BaseModel):
  text: str = Field(min_length=1, max_length=5000)
  memory_type: str = Field(default="journal_insight", max_length=64)
  importance: float = Field(default=0.5, ge=0.0, le=1.0)
  source_date: Optional[date] = None
  goal_id: Optional[int] = None


class UserSettingsUpdate(BaseModel):
  name: Optional[str] = None
  birth_date: Optional[str] = None
  target_age: Optional[int] = Field(default=None, ge=18, le=120)
  custom_coach_prompt: Optional[str] = Field(default=None, max_length=2000)
  preferred_tone: Optional[str] = None
  remote_ai_consent: Optional[bool] = None


def require_api_token(authorization: Optional[str] = Header(default=None)) -> None:
  """Protect hosted deployments while keeping a token-free local developer mode."""
  token = settings.GOALOS_API_TOKEN
  if not token:
    return
  supplied = authorization.removeprefix("Bearer ").strip() if authorization else ""
  if not hmac.compare_digest(supplied, token):
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing bearer token")


@app.middleware("http")
async def limit_request_body(request: Request, call_next):
  content_length = request.headers.get("content-length")
  if content_length and int(content_length) > MAX_REQUEST_BYTES:
    return JSONResponse(status_code=413, content={"detail": "Request body is too large"})
  return await call_next(request)


@app.on_event("startup")
def startup() -> None:
  if settings.ENVIRONMENT.lower() == "production" and not settings.GOALOS_API_TOKEN:
    raise RuntimeError("GOALOS_API_TOKEN is required when ENVIRONMENT=production")
  try:
    from services.demo_seeder import seed_demo_environment
    seed_demo_environment()
  except Exception as e:
    logger.warning("Demo initialization on startup skipped: %s", e)
  run_migrations()



# ---------------------------------------------------------------------------
# Health & Status
# ---------------------------------------------------------------------------


@api_router.get("/health")
def health() -> dict:
  return {"status": "ok"}



@api_router.get("/health/details", dependencies=[Depends(require_api_token)])
def health_details() -> dict:
  return {
    "status": "ok",
    "openrouter_configured": bool(settings.OPENROUTER_API_KEY),
    "remote_ai_consent": SettingsService().remote_ai_allowed(),
    "log_count": LogRepository().count(),
    "memory_count": MemoryService().count(),
    "goal_count": len(GoalRepository().get_all()),
  }


# ---------------------------------------------------------------------------
# Life Calendar
# ---------------------------------------------------------------------------


def _get_user_calendar_service() -> LifeCalendarService:
  with get_db() as conn:
    row = conn.execute("SELECT birth_date, target_age FROM user WHERE id = 1").fetchone()
  if row:
    birth_str = row["birth_date"] or "2002-06-17"
    target_age = row["target_age"] or 70
  else:
    birth_str = "2002-06-17"
    target_age = 70
  return LifeCalendarService(birth_date=birth_str, target_age=int(target_age))


@api_router.get("/calendar/summary", dependencies=[Depends(require_api_token)])
def calendar_summary(reference_date: Optional[date] = None) -> dict:
  service = _get_user_calendar_service()
  return service.get_summary(reference_date=reference_date)


@api_router.get("/calendar/grid", dependencies=[Depends(require_api_token)])
def calendar_grid(reference_date: Optional[date] = None) -> list:
  service = _get_user_calendar_service()
  return service.get_grid_data(reference_date=reference_date)


@api_router.get("/calendar/year", dependencies=[Depends(require_api_token)])
def calendar_year(
  year: Optional[int] = None, reference_date: Optional[date] = None
) -> dict:
  service = _get_user_calendar_service()
  return service.get_year_productivity_grid(year=year, reference_date=reference_date)



# ---------------------------------------------------------------------------
# Journal & Daily Logs
# ---------------------------------------------------------------------------


def _refresh_month_snapshot(month: str) -> None:
  """Keep the stored month in step with the data. Facts only: the lever analysis runs on import/recompute."""
  try:
    MonthlyAnalyticsService().recompute_month(month, with_insights=False)
  except Exception as exc:
    logger.warning("Failed to refresh monthly snapshot %s: %s", month, exc)


def _rescore_all(reason: str) -> None:
  """Scores read task links and goal cues, so changing either re-scores every day (about 90 rows, cheap)."""
  try:
    from services.analytics_service import recompute_all_scores

    recompute_all_scores()
    MonthlyAnalyticsService().recompute_all(with_insights=False)  # facts only; levers don't read these scores
  except Exception as exc:
    logger.warning("Failed to re-score after %s: %s", reason, exc)


@api_router.get("/journal/today", dependencies=[Depends(require_api_token)])
def journal_today() -> dict:
  today = date.today()
  repo = LogRepository()
  log = repo.get_by_date(today)
  if not log:
    return DailyLog(id=0, date=today).model_dump(mode="json")
  return log.model_dump(mode="json")


@api_router.get("/journal/date/{target_date}", dependencies=[Depends(require_api_token)])
def journal_get_by_date(target_date: date) -> dict:
  repo = LogRepository()
  log = repo.get_by_date(target_date)
  if not log:
    return DailyLog(id=0, date=target_date).model_dump(mode="json")
  return log.model_dump(mode="json")


@api_router.post("/journal/upsert", dependencies=[Depends(require_api_token)])
def journal_upsert(payload: dict) -> dict:
  target_date_str = payload.get("date")
  if not target_date_str:
    target_date = date.today()
  else:
    target_date = date.fromisoformat(target_date_str) if isinstance(target_date_str, str) else target_date_str

  update_data = {k: v for k, v in payload.items() if k != "date"}
  changes = DailyLogUpdate(**update_data)
  log = LogRepository().upsert_fields(target_date, changes)

  # Automatically update daily scores
  try:
    from services.analytics_service import recompute_all_scores
    # This day's score, and the later days whose 14-day window or momentum includes it.
    recompute_all_scores(since=target_date)
  except Exception as exc:
    logger.warning("Failed to calculate daily score on journal upsert: %s", exc)

  _refresh_month_snapshot(f"{target_date.year:04d}-{target_date.month:02d}")

  return log.model_dump(mode="json")


@api_router.get("/journal/history", dependencies=[Depends(require_api_token)])
def journal_history(limit: int = Query(default=30, ge=1, le=365)) -> list[dict]:
  logs = LogRepository().get_recent(last_n=limit)
  return [log.model_dump(mode="json") for log in logs]


# ---------------------------------------------------------------------------
# Goals & Milestones
# ---------------------------------------------------------------------------


@api_router.get("/goals", dependencies=[Depends(require_api_token)])
def get_goals(
  status: Optional[str] = None,
  category: Optional[str] = None,
  horizon: Optional[str] = None,
) -> list[dict]:
  goals = GoalRepository().get_all(status=status, category=category, horizon=horizon)
  result = []
  milestone_repo = MilestoneRepository()
  for g in goals:
    g_dict = g.model_dump(mode="json")
    g_dict["milestones"] = [m.model_dump(mode="json") for m in milestone_repo.get_for_goal(g.id)]
    result.append(g_dict)
  return result


@api_router.get("/goals/horizons", dependencies=[Depends(require_api_token)])
def get_goals_horizons() -> dict[str, list[dict]]:
  categorized = GoalRepository().get_by_horizons()
  milestone_repo = MilestoneRepository()
  output: dict[str, list[dict]] = {}
  for horizon, goals in categorized.items():
    horizon_list = []
    for g in goals:
      g_dict = g.model_dump(mode="json")
      g_dict["milestones"] = [m.model_dump(mode="json") for m in milestone_repo.get_for_goal(g.id)]
      horizon_list.append(g_dict)
    output[horizon] = horizon_list
  return output


@api_router.get("/tasks/review", dependencies=[Depends(require_api_token)])
def get_task_review_queue(limit: int = Query(default=50, ge=1, le=500)) -> dict:
  """Completed tasks whose goal is still unknown, most-repeated first."""
  return TaskLinkService().review_queue(limit=limit)


@api_router.put("/tasks/links", dependencies=[Depends(require_api_token)])
def put_task_link(payload: TaskLinkWrite) -> dict:
  """Say which goal a task serves (or that it serves none). The decision applies to every day it appears."""
  try:
    key = TaskLinkService().set_link(payload.key, payload.kind, payload.goal_id)
  except LookupError:
    raise HTTPException(status_code=404, detail="Goal not found") from None
  except ValueError as exc:
    raise HTTPException(status_code=422, detail=str(exc)) from exc
  _rescore_all("task link saved")
  return {"key": key, "kind": payload.kind, "goal_id": payload.goal_id}


@api_router.delete("/tasks/links/{key}", dependencies=[Depends(require_api_token)])
def delete_task_link(key: str) -> dict:
  if not TaskLinkService().clear_link(key):
    raise HTTPException(status_code=404, detail="No saved link for that task")
  _rescore_all("task link removed")
  return {"success": True}


@api_router.get("/goals/pacing", dependencies=[Depends(require_api_token)])
def get_goals_pacing(horizon: Optional[str] = Query(default=None, pattern=r"^(1-year|5-year|10-year)$")) -> list[dict]:
  """Pace of yearly-and-beyond goals against their numeric targets and monthly check-ins."""
  return YearlyPacingService().evaluate_all(horizon=horizon)


@api_router.get("/goals/attention", dependencies=[Depends(require_api_token)])
def get_goals_attention(days: int = Query(default=14, ge=1, le=90)) -> list[dict]:
  """Completed tasks per active goal over the last `days` days, and how long each has been quiet."""
  return TaskLinkService().goal_attention(days=days)


@api_router.get("/goals/{goal_id}", dependencies=[Depends(require_api_token)])
def get_goal(goal_id: int) -> dict:
  goal = GoalRepository().get_by_id(goal_id)
  if not goal:
    raise HTTPException(status_code=404, detail="Goal not found")
  g_dict = goal.model_dump(mode="json")
  g_dict["milestones"] = [m.model_dump(mode="json") for m in MilestoneRepository().get_for_goal(goal_id)]
  return g_dict


@api_router.post("/goals", dependencies=[Depends(require_api_token)])
def create_goal(goal_in: GoalCreate) -> dict:
  created = GoalRepository().create(goal_in)
  if created.cues:
    _rescore_all("goal created with cues")
  _refresh_month_snapshot(date.today().strftime("%Y-%m"))
  return created.model_dump(mode="json")


@api_router.put("/goals/{goal_id}", dependencies=[Depends(require_api_token)])
def update_goal(goal_id: int, goal_in: GoalUpdate) -> dict:
  updated = GoalRepository().update(goal_id, goal_in)
  if not updated:
    raise HTTPException(status_code=404, detail="Goal not found")
  if goal_in.cues is not None:
    _rescore_all("goal cues changed")
  _refresh_month_snapshot(date.today().strftime("%Y-%m"))
  return updated.model_dump(mode="json")


@api_router.delete("/goals/{goal_id}", dependencies=[Depends(require_api_token)])
def delete_goal(goal_id: int) -> dict:
  success = GoalRepository().delete(goal_id)
  if not success:
    raise HTTPException(status_code=404, detail="Goal not found")
  _rescore_all("goal deleted")  # its task links went with it
  return {"success": True}


def _require_goal(goal_id: int) -> None:
  if GoalRepository().get_by_id(goal_id) is None:
    raise HTTPException(status_code=404, detail="Goal not found")


@api_router.get("/goals/{goal_id}/measurements", dependencies=[Depends(require_api_token)])
def list_goal_measurements(goal_id: int) -> list[dict]:
  _require_goal(goal_id)
  return [m.model_dump(mode="json") for m in MonthlyRepository().get_measurements(goal_id)]


@api_router.put("/goals/{goal_id}/measurements", dependencies=[Depends(require_api_token)])
def put_goal_measurement(goal_id: int, measurement: GoalMeasurementCreate) -> dict:
  _require_goal(goal_id)
  return MonthlyRepository().upsert_measurement(goal_id, measurement).model_dump(mode="json")


@api_router.delete("/goals/{goal_id}/measurements/{month}", dependencies=[Depends(require_api_token)])
def delete_goal_measurement(goal_id: int, month: str = PathParam(pattern=MONTH_PATTERN)) -> dict:
  _require_goal(goal_id)
  if not MonthlyRepository().delete_measurement(goal_id, month):
    raise HTTPException(status_code=404, detail="Check-in not found")
  return {"success": True}


@api_router.get("/goals/{goal_id}/pace-points", dependencies=[Depends(require_api_token)])
def list_goal_pace_points(goal_id: int) -> list[dict]:
  _require_goal(goal_id)
  return [p.model_dump(mode="json") for p in MonthlyRepository().get_pace_points(goal_id)]


@api_router.put("/goals/{goal_id}/pace-points", dependencies=[Depends(require_api_token)])
def put_goal_pace_point(goal_id: int, point: GoalPacePointCreate) -> dict:
  _require_goal(goal_id)
  return MonthlyRepository().upsert_pace_point(goal_id, point).model_dump(mode="json")


@api_router.delete("/goals/{goal_id}/pace-points/{due}", dependencies=[Depends(require_api_token)])
def delete_goal_pace_point(goal_id: int, due: date) -> dict:
  _require_goal(goal_id)
  if not MonthlyRepository().delete_pace_point(goal_id, due):
    raise HTTPException(status_code=404, detail="Pace point not found")
  return {"success": True}


@api_router.post("/goals/{goal_id}/milestones", dependencies=[Depends(require_api_token)])
def create_milestone(goal_id: int, milestone_in: MilestoneCreate) -> dict:
  if milestone_in.goal_id != goal_id:
    milestone_in.goal_id = goal_id
  try:
    created = MilestoneRepository().create(milestone_in)
    return created.model_dump(mode="json")
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc


@api_router.put("/milestones/{milestone_id}", dependencies=[Depends(require_api_token)])
@api_router.patch("/milestones/{milestone_id}", dependencies=[Depends(require_api_token)])
def update_milestone(milestone_id: int, milestone_in: MilestoneUpdate) -> dict:
  updated = MilestoneRepository().update(milestone_id, milestone_in)
  if not updated:
    raise HTTPException(status_code=404, detail="Milestone not found")
  return updated.model_dump(mode="json")


@api_router.delete("/milestones/{milestone_id}", dependencies=[Depends(require_api_token)])
def delete_milestone(milestone_id: int) -> dict:
  success = MilestoneRepository().delete(milestone_id)
  if not success:
    raise HTTPException(status_code=404, detail="Milestone not found")
  return {"success": True}


# ---------------------------------------------------------------------------
# AI Coaching Suite
# ---------------------------------------------------------------------------


@api_router.post("/coach/future-self", dependencies=[Depends(require_api_token)])
def coach_future_self(payload: dict) -> dict:
  target_date_str = payload.get("date")
  target_date = date.fromisoformat(target_date_str) if target_date_str else date.today()
  try:
    return CoachService().get_future_self_coaching(target_date)
  except Exception:
    logger.exception("future_self_coach_failed event=api")
    raise HTTPException(status_code=500, detail="Unable to generate future self coaching") from None


@api_router.post("/coach/progress", dependencies=[Depends(require_api_token)])
def coach_progress(payload: dict) -> dict:
  target_date_str = payload.get("date")
  target_date = date.fromisoformat(target_date_str) if target_date_str else date.today()
  try:
    return CoachService().get_progress_coaching(target_date)
  except Exception:
    logger.exception("progress_coach_failed event=api")
    raise HTTPException(status_code=500, detail="Unable to generate goal alignment coaching") from None


# ---------------------------------------------------------------------------
# Multi-Agent Coordinator & Session Management
# ---------------------------------------------------------------------------


@api_router.post("/coach/chat", dependencies=[Depends(require_api_token)], response_model=CoachChatResponse)
def coach_chat(req: CoachChatRequest) -> CoachChatResponse:
  """Conversational coordinator agent with multi-agent triage and scoped tools."""
  try:
    pipeline = CoordinatorPipeline()
    return pipeline.chat(req)
  except Exception:
    logger.exception("coach_chat_failed event=api")
    raise HTTPException(status_code=500, detail="Coordinator coaching failed") from None


@api_router.get("/coach/sessions", dependencies=[Depends(require_api_token)], response_model=list[CoachSessionRead])
def list_coach_sessions(limit: int = Query(default=30, ge=1, le=100)) -> list[CoachSessionRead]:
  """List recent persistent coaching sessions."""
  return CoachSessionRepository().list_sessions(limit=limit)


@api_router.post("/coach/sessions", dependencies=[Depends(require_api_token)], response_model=CoachSessionRead)
def create_coach_session(req: CoachSessionCreate) -> CoachSessionRead:
  """Create a new conversational coaching session with optional blackboard state."""
  return CoachSessionRepository().create_session(
    title=req.title,
    intent=req.intent,
    active_horizon_id=req.active_horizon_id,
    blackboard=req.blackboard,
  )


@api_router.get("/coach/sessions/{session_id}", dependencies=[Depends(require_api_token)], response_model=CoachSessionRead)
def get_coach_session(session_id: str) -> CoachSessionRead:
  """Get full session conversation history and blackboard state."""
  session = CoachSessionRepository().get_session(session_id)
  if not session:
    raise HTTPException(status_code=404, detail="Coaching session not found")
  return session


@api_router.delete("/coach/sessions/{session_id}", dependencies=[Depends(require_api_token)])
def delete_coach_session(session_id: str) -> dict:
  """Delete a coaching session and its message history."""
  deleted = CoachSessionRepository().delete_session(session_id)
  if not deleted:
    raise HTTPException(status_code=404, detail="Coaching session not found")
  return {"success": True}


# ---------------------------------------------------------------------------
# Observability & Cost Telemetry
# ---------------------------------------------------------------------------


@api_router.get("/coach/telemetry/summary", dependencies=[Depends(require_api_token)], response_model=TelemetrySummaryResponse)
def get_telemetry_summary(days: int = Query(default=30, ge=1, le=365)) -> TelemetrySummaryResponse:
  """Get aggregated AI token consumption, latency, and estimated USD spend."""
  return ObservabilityService().get_summary(days=days)


@api_router.get("/coach/telemetry/traces", dependencies=[Depends(require_api_token)], response_model=list[TelemetrySpan])
def get_telemetry_traces(limit: int = Query(default=25, ge=1, le=100)) -> list[TelemetrySpan]:
  """Get recent AI execution spans and latency metrics."""
  return ObservabilityService().get_recent_traces(limit=limit)


# ---------------------------------------------------------------------------
# Memories (Hybrid RAG)
# ---------------------------------------------------------------------------


@api_router.get("/memories/search", dependencies=[Depends(require_api_token)])
def memories_search(q: str = Query(min_length=1), limit: int = Query(default=10, ge=1, le=50)) -> list[dict]:
  try:
    results = MemoryService().retrieve_scored(q, top_k=limit)
    return [{**memory.model_dump(mode="json"), "score": score} for memory, score in results]
  except Exception as exc:
    logger.warning("memory_search_failed: %s", exc)
    return []


@api_router.get("/memories", dependencies=[Depends(require_api_token)])
def memories_list(
  limit: int = Query(default=50, ge=1, le=200),
  memory_type: Optional[str] = None,
) -> list[dict]:
  memories = MemoryRepository().get_all(memory_type=memory_type)[:limit]
  return [m.model_dump(mode="json") for m in memories]


@api_router.post("/memories", dependencies=[Depends(require_api_token)])
def memories_create(req: MemoryStoreRequest) -> dict:
  mem = MemoryService().store(
    text=req.text,
    memory_type=req.memory_type,
    importance=req.importance,
    source_date=req.source_date,
    source_type="goal" if req.goal_id else None,
    source_id=req.goal_id,
  )
  return mem.model_dump(mode="json")


@api_router.delete("/memories/{memory_id}", dependencies=[Depends(require_api_token)])
def memories_delete(memory_id: int) -> dict:
  success = MemoryRepository().delete(memory_id)
  if not success:
    raise HTTPException(status_code=404, detail="Memory not found")
  return {"success": True}


# ---------------------------------------------------------------------------
# Analytics & Performance
# ---------------------------------------------------------------------------


@api_router.get("/analytics/dashboard", dependencies=[Depends(require_api_token)])
def analytics_dashboard() -> dict:
  log_repo = LogRepository()
  score_repo = ScoreRepository()
  goal_repo = GoalRepository()
  recent_logs = log_repo.get_recent(last_n=30)
  recent_scores = score_repo.get_recent(last_n=30)
  active_goals = goal_repo.get_active()

  pattern_cards = []
  try:
    analysis = PatternService().analyze_patterns(recent_logs, active_goals)
    for p in analysis.get("repeating_unhealthy_patterns", []):
      dates = p.get("dates_observed", [])
      date_str = f" ({', '.join(dates[:3])})" if dates else ""
      pattern_cards.append({
        "title": p.get("pattern_name", "Friction Pattern"),
        "description": f"{p.get('occurrences_count', 1)}x recorded{date_str}. Action: {p.get('actionable_countermeasure', '')}",
        "pattern_type": "warning",
      })
    for p in analysis.get("compounding_healthy_patterns", []):
      pattern_cards.append({
        "title": p.get("pattern_name", "Momentum Pattern"),
        "description": f"{p.get('evidence', '')} Rule: {p.get('reinforcement_rule', '')}",
        "pattern_type": "healthy",
      })
    for f in analysis.get("isolated_friction_events", []):
      pattern_cards.append({
        "title": f.get("event_name", "Isolated Event"),
        "description": f"Observed on {f.get('date_observed')}: {f.get('actionable_note', '')}",
        "pattern_type": "warning",
      })
  except Exception as exc:
    logger.warning("Failed to analyze multi-day patterns: %s", exc)
    pattern_cards = []

  total_logs = len(recent_logs)
  sleep_logs = [l.sleep_hours for l in recent_logs if l.sleep_hours is not None]

  avg_sleep = round(sum(sleep_logs) / len(sleep_logs), 1) if sleep_logs else 0.0

  return {
    "total_logs": total_logs,
    "avg_sleep_hours": avg_sleep,
    "patterns": pattern_cards,
    "recent_scores": [s.model_dump(mode="json") for s in recent_scores],
  }


@api_router.get("/analytics/scores", dependencies=[Depends(require_api_token)])
def analytics_scores(limit: int = Query(default=30, ge=1, le=180)) -> list[dict]:
  scores = ScoreRepository().get_recent(last_n=limit)
  return [s.model_dump(mode="json") for s in scores]


def _snapshot_payload(service: MonthlyAnalyticsService, snapshot) -> dict:
  payload = snapshot.model_dump(mode="json")
  payload["goal_results"] = [r.model_dump(mode="json") for r in service.get_goal_results(snapshot.month)]
  return payload


@api_router.get("/analytics/monthly", dependencies=[Depends(require_api_token)])
def analytics_monthly() -> list[dict]:
  """Stored month-by-month analytics, oldest first. Built on first read if nothing is stored yet."""
  service = MonthlyAnalyticsService()
  return [_snapshot_payload(service, s) for s in service.snapshots_ensuring_built()]


@api_router.post("/analytics/monthly/recompute", dependencies=[Depends(require_api_token)])
def analytics_monthly_recompute(month: Optional[str] = Query(default=None, pattern=MONTH_PATTERN)) -> dict:
  service = MonthlyAnalyticsService()
  if month is None:
    return {"recomputed": [s.month for s in service.recompute_all()]}
  snapshot = service.recompute_month(month)
  if snapshot is None:
    raise HTTPException(status_code=404, detail="No journal entries for that month")
  return _snapshot_payload(service, snapshot)


@api_router.get("/analytics/monthly/{month}", dependencies=[Depends(require_api_token)])
def analytics_monthly_one(month: str = PathParam(pattern=MONTH_PATTERN)) -> dict:
  service = MonthlyAnalyticsService()
  snapshot = service.get_snapshot(month)
  if snapshot is None:
    raise HTTPException(status_code=404, detail="No stored analytics for that month")
  return _snapshot_payload(service, snapshot)


# ---------------------------------------------------------------------------
# Settings & Portability
# ---------------------------------------------------------------------------


@api_router.get("/settings", dependencies=[Depends(require_api_token)])
def get_user_settings() -> dict:
  with get_db() as conn:
    row = conn.execute("SELECT * FROM user WHERE id = 1").fetchone()
  user_dict = dict(row) if row else {}
  settings_service = SettingsService()
  user_dict["remote_ai_consent"] = settings_service.remote_ai_allowed()
  user_dict["openrouter_configured"] = bool(settings.OPENROUTER_API_KEY)
  user_dict["environment"] = settings.ENVIRONMENT
  return user_dict


@api_router.post("/settings", dependencies=[Depends(require_api_token)])
def update_user_settings(req: UserSettingsUpdate) -> dict:
  settings_service = SettingsService()
  if req.remote_ai_consent is not None:
    settings_service.set_remote_ai_allowed(req.remote_ai_consent)

  updates: list[str] = []
  params: list[Any] = []
  if req.name is not None:
    updates.append("name = ?")
    params.append(req.name)
  if req.birth_date is not None:
    updates.append("birth_date = ?")
    params.append(req.birth_date)
  if req.target_age is not None:
    updates.append("target_age = ?")
    params.append(req.target_age)
  if req.custom_coach_prompt is not None:
    updates.append("custom_coach_prompt = ?")
    params.append(req.custom_coach_prompt.strip() or None)
  if req.preferred_tone is not None:
    updates.append("preferred_tone = ?")
    params.append(req.preferred_tone.strip() or None)

  if updates:
    updates.append("updated_at = CURRENT_TIMESTAMP")
    sql = f"UPDATE user SET {', '.join(updates)} WHERE id = 1"
    with get_db() as conn:
      conn.execute(sql, params)

  return get_user_settings()


@api_router.get("/export", dependencies=[Depends(require_api_token)])
def export_data() -> JSONResponse:
  return JSONResponse(content=DataPortabilityService().export_payload())


@api_router.get("/export/weekly-report", dependencies=[Depends(require_api_token)])
def export_weekly_report(
  week_start_date: Optional[str] = Query(default=None),
  format: str = Query(default="markdown", pattern="^(markdown|html|json)$"),
):
  """Compile a 7-day retrospective digest as Markdown, printable HTML, or raw JSON."""
  try:
    week_start = date.fromisoformat(week_start_date) if week_start_date else None
  except ValueError:
    raise HTTPException(status_code=400, detail="week_start_date must be an ISO date (YYYY-MM-DD)") from None

  service = ReportService()
  try:
    report = service.build_report(week_start)
  except Exception:
    logger.exception("weekly_report_failed event=api")
    raise HTTPException(status_code=500, detail="Unable to compile the weekly digest") from None

  filename = f"goalos_weekly_digest_{report['week_start']}"
  if format == "json":
    return JSONResponse(content=report)
  if format == "html":
    return HTMLResponse(
      content=service.render_html(report),
      headers={"Content-Disposition": f'inline; filename="{filename}.html"'},
    )
  return PlainTextResponse(
    content=service.render_markdown(report),
    media_type="text/markdown; charset=utf-8",
    headers={"Content-Disposition": f'attachment; filename="{filename}.md"'},
  )


@api_router.post("/export/reset", dependencies=[Depends(require_api_token)])
def factory_reset(payload: dict) -> dict:
  confirmation = payload.get("confirmation", "")
  if confirmation != "RESET":
    raise HTTPException(status_code=400, detail="Confirmation phrase 'RESET' is required")
  backup_path = DataPortabilityService().safe_factory_reset()
  return {"success": True, "backup_created": str(backup_path)}


# ---------------------------------------------------------------------------
# Mount API Router (Canonical /api and Root Compatibility)
# ---------------------------------------------------------------------------
app.include_router(api_router, prefix="/api")
app.include_router(api_router, include_in_schema=False)


# ---------------------------------------------------------------------------
# Frontend Static Mount (/app) & Root Redirect
# ---------------------------------------------------------------------------
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

FRONTEND_DIST = os.path.join(ROOT, "frontend", "dist")
if os.path.exists(FRONTEND_DIST):
  assets_dir = os.path.join(FRONTEND_DIST, "assets")
  if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

  # The SPA lives at /app but its bundles live at /assets, so the PWA service
  # worker and manifest must be served from root to get root scope.
  @app.get("/sw.js", include_in_schema=False)
  @app.get("/registerSW.js", include_in_schema=False)
  @app.get("/index.html", include_in_schema=False)
  @app.get("/workbox-{suffix}.js", include_in_schema=False)
  @app.get("/manifest.webmanifest", include_in_schema=False)
  @app.get("/favicon.svg", include_in_schema=False)
  def serve_pwa_root_file(request: Request, suffix: str = ""):
    candidate = os.path.normpath(os.path.join(FRONTEND_DIST, request.url.path.lstrip("/")))
    if not candidate.startswith(FRONTEND_DIST) or not os.path.isfile(candidate):
      raise HTTPException(status_code=404, detail="Not found")
    headers = {"Service-Worker-Allowed": "/"} if candidate.endswith(".js") else None
    return FileResponse(candidate, headers=headers)

  @app.get("/app", include_in_schema=False)
  @app.get("/app/{full_path:path}", include_in_schema=False)
  def serve_frontend(full_path: str = ""):
    index_file = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.exists(index_file):
      return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="UI not found")


@app.get("/", include_in_schema=False)
def root_redirect():
  if os.path.exists(os.path.join(ROOT, "frontend", "dist", "index.html")):
    return RedirectResponse(url="/app")
  return RedirectResponse(url="/docs")

