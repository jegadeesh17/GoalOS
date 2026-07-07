"""GoalOS FastAPI — morning coaching and health endpoints."""

from __future__ import annotations

import os
import sys
from datetime import date

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config.settings import settings
from database.migrations import run_migrations
from database.repositories.log_repository import LogRepository
from models.daily_log import DailyLogCreate
from services.coach_service import CoachService
from services.journal_helpers import serialize_journal_fields
from services.memory_service import MemoryService

app = FastAPI(title="GoalOS Coaching API", version="1.0.0")


class TaskInput(BaseModel):
    text: str
    priority: int = 1
    completed: bool = False


class MorningCoachRequest(BaseModel):
    target_date: date | None = None
    gratitude: str = ""
    plans_text: str = ""
    tasks: list[TaskInput] = Field(default_factory=lambda: [TaskInput(text="Deep work block", priority=1)])
    sleep_hours: float | None = None
    sleep_quality: int | None = Field(default=None, ge=1, le=5)
    mood_morning: int | None = Field(default=None, ge=1, le=5)


@app.on_event("startup")
def startup() -> None:
    run_migrations()


@app.get("/health")
def health() -> dict:
    log_repo = LogRepository()
    memory = MemoryService()
    return {
        "status": "ok",
        "openrouter_configured": bool(settings.OPENROUTER_API_KEY),
        "log_count": log_repo.count(),
        "memory_count": memory.count(),
    }


@app.post("/coach/morning")
def coach_morning(req: MorningCoachRequest) -> dict:
    target_date = req.target_date or date.today()
    fields = serialize_journal_fields(
        req.gratitude,
        req.plans_text,
        [task.model_dump() for task in req.tasks],
    )
    log = LogRepository().upsert_by_date(
        DailyLogCreate(
            date=target_date,
            morning_completed=True,
            sleep_hours=req.sleep_hours,
            sleep_quality=req.sleep_quality,
            mood_morning=req.mood_morning,
            **fields,
        )
    )
    try:
        return CoachService().get_morning_coaching(target_date, log)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
