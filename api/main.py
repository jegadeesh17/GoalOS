"""GoalOS FastAPI surface with optional single-user bearer protection."""

from __future__ import annotations

import hmac
import logging
import os
import sys
from datetime import date

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
  sys.path.insert(0, ROOT)

from config.settings import settings
from database.migrations import run_migrations
from database.repositories.log_repository import LogRepository
from models.daily_log import DailyLogUpdate
from services.coach_service import CoachService
from services.data_portability_service import DataPortabilityService
from services.journal_helpers import serialize_journal_fields
from services.memory_service import MemoryService

logger = logging.getLogger(__name__)
MAX_REQUEST_BYTES = 64 * 1024
app = FastAPI(title="GoalOS Coaching API", version="2.0.0")


class TaskInput(BaseModel):
  id: str | None = Field(default=None, min_length=1, max_length=64)
  text: str = Field(min_length=1, max_length=500)
  priority: int = Field(default=1, ge=1, le=100)
  completed: bool = False
  goal_id: int | None = Field(default=None, ge=1)
  milestone_id: int | None = Field(default=None, ge=1)


class MorningCoachRequest(BaseModel):
  target_date: date | None = None
  gratitude: str = Field(default="", max_length=2000)
  plans_text: str = Field(default="", max_length=6000)
  tasks: list[TaskInput] = Field(min_length=1, max_length=25)
  sleep_hours: float | None = Field(default=None, ge=0, le=24)
  sleep_quality: int | None = Field(default=None, ge=1, le=5)
  mood_morning: int | None = Field(default=None, ge=1, le=5)


def require_api_token(authorization: str | None = Header(default=None)) -> None:
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


@app.get("/health")
def health() -> dict:
  return {"status": "ok"}


@app.get("/health/details", dependencies=[Depends(require_api_token)])
def health_details() -> dict:
  return {
    "status": "ok",
    "openrouter_configured": bool(settings.OPENROUTER_API_KEY),
    "remote_ai_consent": CoachService().settings_service.remote_ai_allowed(),
    "log_count": LogRepository().count(),
    "memory_count": MemoryService().count(),
  }


@app.get("/export", dependencies=[Depends(require_api_token)])
def export_data() -> JSONResponse:
  return JSONResponse(content=DataPortabilityService().export_payload())


@app.post("/coach/morning", dependencies=[Depends(require_api_token)])
def coach_morning(req: MorningCoachRequest) -> dict:
  target_date = req.target_date or date.today()
  try:
    fields = serialize_journal_fields(req.gratitude, req.plans_text, [task.model_dump() for task in req.tasks])
    changes = DailyLogUpdate(
      morning_completed=True,
      sleep_hours=req.sleep_hours,
      sleep_quality=req.sleep_quality,
      mood_morning=req.mood_morning,
      **fields,
    )
    log = LogRepository().upsert_fields(target_date, changes)
    return CoachService().get_morning_coaching(target_date, log)
  except ValueError as exc:
    raise HTTPException(status_code=422, detail=str(exc)) from exc
  except Exception:
    logger.exception("morning_coach_failed event=api")
    raise HTTPException(status_code=500, detail="Unable to generate coaching right now")
