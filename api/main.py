"""GoalOS FastAPI surface with CORS, REST CRUD for all domains, and coaching pipelines."""

from __future__ import annotations

import hmac
import json
import logging
import os
import sys
from datetime import date
from typing import Any, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
  sys.path.insert(0, ROOT)

from config.settings import settings
from database.connection import get_db
from database.migrations import run_migrations
from database.repositories.coach_repository import CoachRepository
from database.repositories.goal_repository import GoalRepository
from database.repositories.log_repository import LogRepository
from database.repositories.memory_repository import MemoryRepository
from database.repositories.milestone_repository import MilestoneRepository
from database.repositories.score_repository import ScoreRepository
from models.daily_log import DailyLog, DailyLogUpdate
from models.goal import Goal, GoalCreate, GoalUpdate
from models.milestone import Milestone, MilestoneCreate, MilestoneUpdate
from services.coach_service import CoachService
from services.data_portability_service import DataPortabilityService
from services.journal_helpers import serialize_journal_fields
from services.life_calendar_service import LifeCalendarService
from services.memory_service import MemoryService
from services.pattern_service import PatternService
from services.settings_service import SettingsService

logger = logging.getLogger(__name__)
MAX_REQUEST_BYTES = 512 * 1024

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


# ---------------------------------------------------------------------------
# Request & Response Schemas
# ---------------------------------------------------------------------------


class TaskInput(BaseModel):
  id: Optional[str] = Field(default=None, max_length=64)
  text: str = Field(min_length=1, max_length=500)
  priority: int = Field(default=1, ge=1, le=100)
  completed: bool = False
  goal_id: Optional[int] = Field(default=None, ge=1)
  milestone_id: Optional[int] = Field(default=None, ge=1)


class MorningCoachRequest(BaseModel):
  target_date: Optional[date] = None
  gratitude: str = Field(default="", max_length=2000)
  plans_text: str = Field(default="", max_length=6000)
  tasks: list[TaskInput] = Field(default_factory=list, max_length=50)
  sleep_hours: Optional[float] = Field(default=None, ge=0, le=24)
  sleep_quality: Optional[int] = Field(default=None, ge=1, le=5)
  mood_morning: Optional[int] = Field(default=None, ge=1, le=5)
  energy_level: Optional[int] = Field(default=None, ge=1, le=5)
  expected_focus: Optional[int] = Field(default=None, ge=1, le=5)
  intention: Optional[str] = Field(default="", max_length=2000)
  anxiety: Optional[str] = Field(default="", max_length=2000)
  top_priority: Optional[str] = Field(default="", max_length=1000)


class EveningCoachRequest(BaseModel):
  target_date: Optional[date] = None
  journal_entry: str = Field(default="", max_length=8000)
  deep_work_hours: Optional[float] = Field(default=None, ge=0, le=24)
  mood_evening: Optional[int] = Field(default=None, ge=1, le=5)
  one_win: Optional[str] = Field(default="", max_length=2000)
  one_lesson: Optional[str] = Field(default="", max_length=2000)
  takeaway: Optional[str] = Field(default="", max_length=2000)
  biggest_distraction: Optional[str] = Field(default="", max_length=2000)
  workout_completed: Optional[bool] = None
  tasks_completed: Optional[str] = None
  task_completion_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class MemoryStoreRequest(BaseModel):
  text: str = Field(min_length=1, max_length=5000)
  memory_type: str = Field(default="insight", max_length=64)
  importance: float = Field(default=0.5, ge=0.0, le=1.0)
  source_date: Optional[date] = None
  goal_id: Optional[int] = None


class UserSettingsUpdate(BaseModel):
  name: Optional[str] = None
  birth_date: Optional[str] = None
  target_age: Optional[int] = Field(default=None, ge=18, le=120)
  life_vision: Optional[str] = None
  one_year_vision: Optional[str] = None
  five_year_vision: Optional[str] = None
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
  run_migrations()


# ---------------------------------------------------------------------------
# Health & Status
# ---------------------------------------------------------------------------


@app.get("/health")
def health() -> dict:
  return {"status": "ok"}


@app.get("/health/details", dependencies=[Depends(require_api_token)])
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


@app.get("/calendar/summary", dependencies=[Depends(require_api_token)])
def calendar_summary(reference_date: Optional[date] = None) -> dict:
  service = _get_user_calendar_service()
  return service.get_summary(reference_date=reference_date)


@app.get("/calendar/grid", dependencies=[Depends(require_api_token)])
def calendar_grid(reference_date: Optional[date] = None) -> list:
  service = _get_user_calendar_service()
  return service.get_grid_data(reference_date=reference_date)


# ---------------------------------------------------------------------------
# Journal & Daily Logs
# ---------------------------------------------------------------------------


@app.get("/journal/today", dependencies=[Depends(require_api_token)])
def journal_today() -> dict:
  today = date.today()
  repo = LogRepository()
  log = repo.get_by_date(today)
  if not log:
    log = repo.upsert_fields(today, DailyLogUpdate())
  return log.model_dump(mode="json")


@app.get("/journal/date/{target_date}", dependencies=[Depends(require_api_token)])
def journal_get_by_date(target_date: date) -> dict:
  repo = LogRepository()
  log = repo.get_by_date(target_date)
  if not log:
    log = repo.upsert_fields(target_date, DailyLogUpdate())
  return log.model_dump(mode="json")


@app.post("/journal/upsert", dependencies=[Depends(require_api_token)])
def journal_upsert(payload: dict) -> dict:
  target_date_str = payload.get("date")
  if not target_date_str:
    target_date = date.today()
  else:
    target_date = date.fromisoformat(target_date_str) if isinstance(target_date_str, str) else target_date_str

  update_data = {k: v for k, v in payload.items() if k != "date"}
  changes = DailyLogUpdate(**update_data)
  log = LogRepository().upsert_fields(target_date, changes)
  return log.model_dump(mode="json")


@app.get("/journal/history", dependencies=[Depends(require_api_token)])
def journal_history(limit: int = Query(default=30, ge=1, le=365)) -> list[dict]:
  logs = LogRepository().get_recent(last_n=limit)
  return [log.model_dump(mode="json") for log in logs]


# ---------------------------------------------------------------------------
# Goals & Milestones
# ---------------------------------------------------------------------------


@app.get("/goals", dependencies=[Depends(require_api_token)])
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


@app.get("/goals/horizons", dependencies=[Depends(require_api_token)])
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


@app.get("/goals/{goal_id}", dependencies=[Depends(require_api_token)])
def get_goal(goal_id: int) -> dict:
  goal = GoalRepository().get_by_id(goal_id)
  if not goal:
    raise HTTPException(status_code=404, detail="Goal not found")
  g_dict = goal.model_dump(mode="json")
  g_dict["milestones"] = [m.model_dump(mode="json") for m in MilestoneRepository().get_for_goal(goal_id)]
  return g_dict


@app.post("/goals", dependencies=[Depends(require_api_token)])
def create_goal(goal_in: GoalCreate) -> dict:
  created = GoalRepository().create(goal_in)
  return created.model_dump(mode="json")


@app.put("/goals/{goal_id}", dependencies=[Depends(require_api_token)])
def update_goal(goal_id: int, goal_in: GoalUpdate) -> dict:
  updated = GoalRepository().update(goal_id, goal_in)
  if not updated:
    raise HTTPException(status_code=404, detail="Goal not found")
  return updated.model_dump(mode="json")


@app.delete("/goals/{goal_id}", dependencies=[Depends(require_api_token)])
def delete_goal(goal_id: int) -> dict:
  success = GoalRepository().delete(goal_id)
  if not success:
    raise HTTPException(status_code=404, detail="Goal not found")
  return {"success": True}


@app.post("/goals/{goal_id}/milestones", dependencies=[Depends(require_api_token)])
def create_milestone(goal_id: int, milestone_in: MilestoneCreate) -> dict:
  if milestone_in.goal_id != goal_id:
    milestone_in.goal_id = goal_id
  try:
    created = MilestoneRepository().create(milestone_in)
    return created.model_dump(mode="json")
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.put("/milestones/{milestone_id}", dependencies=[Depends(require_api_token)])
@app.patch("/milestones/{milestone_id}", dependencies=[Depends(require_api_token)])
def update_milestone(milestone_id: int, milestone_in: MilestoneUpdate) -> dict:
  updated = MilestoneRepository().update(milestone_id, milestone_in)
  if not updated:
    raise HTTPException(status_code=404, detail="Milestone not found")
  return updated.model_dump(mode="json")


@app.delete("/milestones/{milestone_id}", dependencies=[Depends(require_api_token)])
def delete_milestone(milestone_id: int) -> dict:
  success = MilestoneRepository().delete(milestone_id)
  if not success:
    raise HTTPException(status_code=404, detail="Milestone not found")
  return {"success": True}


# ---------------------------------------------------------------------------
# AI Coaching Suite
# ---------------------------------------------------------------------------


@app.post("/coach/morning", dependencies=[Depends(require_api_token)])
def coach_morning(req: MorningCoachRequest) -> dict:
  target_date = req.target_date or date.today()
  try:
    task_dicts = [task.model_dump() for task in req.tasks]
    fields = serialize_journal_fields(req.gratitude, req.plans_text, task_dicts)
    changes = DailyLogUpdate(
      morning_completed=True,
      sleep_hours=req.sleep_hours,
      sleep_quality=req.sleep_quality,
      mood_morning=req.mood_morning,
      energy_level=req.energy_level,
      expected_focus=req.expected_focus,
      intention=req.intention,
      anxiety=req.anxiety,
      top_priority=req.top_priority,
      **fields,
    )
    log = LogRepository().upsert_fields(target_date, changes)
    return CoachService().get_morning_coaching(target_date, log)
  except ValueError as exc:
    raise HTTPException(status_code=422, detail=str(exc)) from exc
  except Exception:
    logger.exception("morning_coach_failed event=api")
    raise HTTPException(status_code=500, detail="Unable to generate coaching right now") from None


@app.post("/coach/evening", dependencies=[Depends(require_api_token)])
def coach_evening(req: EveningCoachRequest) -> dict:
  target_date = req.target_date or date.today()
  try:
    changes = DailyLogUpdate(
      evening_completed=True,
      journal_entry=req.journal_entry,
      deep_work_hours=req.deep_work_hours,
      mood_evening=req.mood_evening,
      one_win=req.one_win,
      one_lesson=req.one_lesson,
      takeaway=req.takeaway,
      biggest_distraction=req.biggest_distraction,
      workout_completed=req.workout_completed,
      tasks_completed=req.tasks_completed,
      task_completion_rate=req.task_completion_rate,
    )
    log = LogRepository().upsert_fields(target_date, changes)
    return CoachService().get_evening_coaching(target_date, log)
  except Exception:
    logger.exception("evening_coach_failed event=api")
    raise HTTPException(status_code=500, detail="Unable to generate evening coaching right now") from None


@app.post("/coach/weekly", dependencies=[Depends(require_api_token)])
def coach_weekly(payload: dict) -> dict:
  week_date_str = payload.get("week_start_date")
  week_start = date.fromisoformat(week_date_str) if week_date_str else date.today()
  try:
    return CoachService().get_weekly_coaching(week_start)
  except Exception:
    logger.exception("weekly_coach_failed event=api")
    raise HTTPException(status_code=500, detail="Unable to generate weekly review coaching") from None


@app.post("/coach/future-self", dependencies=[Depends(require_api_token)])
def coach_future_self(payload: dict) -> dict:
  target_date_str = payload.get("date")
  target_date = date.fromisoformat(target_date_str) if target_date_str else date.today()
  try:
    return CoachService().get_future_self_coaching(target_date)
  except Exception:
    logger.exception("future_self_coach_failed event=api")
    raise HTTPException(status_code=500, detail="Unable to generate future self coaching") from None


@app.post("/coach/goal-alignment", dependencies=[Depends(require_api_token)])
def coach_goal_alignment(payload: dict) -> dict:
  goal_id = payload.get("goal_id")
  if not goal_id:
    raise HTTPException(status_code=400, detail="goal_id is required")
  goal = GoalRepository().get_by_id(int(goal_id))
  if not goal:
    raise HTTPException(status_code=404, detail="Goal not found")
  try:
    return CoachService().get_goal_alignment_coaching(goal)
  except Exception:
    logger.exception("goal_alignment_coach_failed event=api")
    raise HTTPException(status_code=500, detail="Unable to generate goal alignment coaching") from None


# ---------------------------------------------------------------------------
# Memories (Hybrid RAG)
# ---------------------------------------------------------------------------


@app.get("/memories/search", dependencies=[Depends(require_api_token)])
def memories_search(q: str = Query(min_length=1), limit: int = Query(default=10, ge=1, le=50)) -> list[dict]:
  try:
    results = MemoryService().hybrid_search(q, top_k=limit)
    return results
  except Exception as exc:
    logger.warning("hybrid_search_failed: %s", exc)
    return []


@app.get("/memories", dependencies=[Depends(require_api_token)])
def memories_list(
  limit: int = Query(default=50, ge=1, le=200),
  memory_type: Optional[str] = None,
) -> list[dict]:
  memories = MemoryRepository().get_all(memory_type=memory_type)[:limit]
  return [m.model_dump(mode="json") for m in memories]


@app.post("/memories", dependencies=[Depends(require_api_token)])
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


@app.delete("/memories/{memory_id}", dependencies=[Depends(require_api_token)])
def memories_delete(memory_id: int) -> dict:
  success = MemoryRepository().delete(memory_id)
  if not success:
    raise HTTPException(status_code=404, detail="Memory not found")
  return {"success": True}


# ---------------------------------------------------------------------------
# Analytics & Performance
# ---------------------------------------------------------------------------


@app.get("/analytics/dashboard", dependencies=[Depends(require_api_token)])
def analytics_dashboard() -> dict:
  log_repo = LogRepository()
  score_repo = ScoreRepository()
  recent_logs = log_repo.get_recent(last_n=30)
  recent_scores = score_repo.get_recent(last_n=30)
  try:
    patterns = PatternService().analyze_multi_day_patterns(limit=14)
  except Exception:
    patterns = []

  total_logs = len(recent_logs)
  avg_sleep = round(sum(l.sleep_hours or 0 for l in recent_logs) / total_logs, 1) if total_logs else 0
  avg_deep_work = round(sum(l.deep_work_hours or 0 for l in recent_logs) / total_logs, 1) if total_logs else 0
  avg_mood = round(sum(l.mood_morning or 3 for l in recent_logs) / total_logs, 1) if total_logs else 0

  return {
    "total_logs": total_logs,
    "avg_sleep_hours": avg_sleep,
    "avg_deep_work_hours": avg_deep_work,
    "avg_morning_mood": avg_mood,
    "patterns": patterns,
    "recent_scores": [s.model_dump(mode="json") for s in recent_scores],
  }


@app.get("/analytics/scores", dependencies=[Depends(require_api_token)])
def analytics_scores(limit: int = Query(default=30, ge=1, le=180)) -> list[dict]:
  scores = ScoreRepository().get_recent(last_n=limit)
  return [s.model_dump(mode="json") for s in scores]


# ---------------------------------------------------------------------------
# Settings & Portability
# ---------------------------------------------------------------------------


@app.get("/settings", dependencies=[Depends(require_api_token)])
def get_user_settings() -> dict:
  with get_db() as conn:
    row = conn.execute("SELECT * FROM user WHERE id = 1").fetchone()
  user_dict = dict(row) if row else {}
  settings_service = SettingsService()
  user_dict["remote_ai_consent"] = settings_service.remote_ai_allowed()
  user_dict["openrouter_configured"] = bool(settings.OPENROUTER_API_KEY)
  user_dict["environment"] = settings.ENVIRONMENT
  return user_dict


@app.post("/settings", dependencies=[Depends(require_api_token)])
def update_user_settings(req: UserSettingsUpdate) -> dict:
  settings_service = SettingsService()
  if req.remote_ai_consent is not None:
    settings_service.set_remote_ai_allowed(req.remote_ai_consent)

  updates = []
  params = []
  if req.name is not None:
    updates.append("name = ?")
    params.append(req.name)
  if req.birth_date is not None:
    updates.append("birth_date = ?")
    params.append(req.birth_date)
  if req.target_age is not None:
    updates.append("target_age = ?")
    params.append(req.target_age)
  if req.life_vision is not None:
    updates.append("life_vision = ?")
    params.append(req.life_vision)
  if req.one_year_vision is not None:
    updates.append("one_year_vision = ?")
    params.append(req.one_year_vision)
  if req.five_year_vision is not None:
    updates.append("five_year_vision = ?")
    params.append(req.five_year_vision)

  if updates:
    updates.append("updated_at = CURRENT_TIMESTAMP")
    sql = f"UPDATE user SET {', '.join(updates)} WHERE id = 1"
    with get_db() as conn:
      conn.execute(sql, params)

  return get_user_settings()


@app.get("/export", dependencies=[Depends(require_api_token)])
def export_data() -> JSONResponse:
  return JSONResponse(content=DataPortabilityService().export_payload())


@app.post("/export/reset", dependencies=[Depends(require_api_token)])
def factory_reset(payload: dict) -> dict:
  confirmation = payload.get("confirmation", "")
  if confirmation != "RESET":
    raise HTTPException(status_code=400, detail="Confirmation phrase 'RESET' is required")
  backup_path = DataPortabilityService().safe_factory_reset()
  return {"success": True, "backup_created": str(backup_path)}
