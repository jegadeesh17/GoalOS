"""Unit tests for Year Productivity Calendar calculations and API endpoints."""

from datetime import date
from fastapi.testclient import TestClient

from api.main import app
from database.repositories.log_repository import LogRepository
from database.repositories.score_repository import ScoreRepository
from models.daily_log import DailyLogCreate
from models.score import ScoreCreate
from services.life_calendar_service import LifeCalendarService


def test_year_productivity_days_count(temp_db):
  service = LifeCalendarService(birth_date=date(2000, 1, 1), target_age=70)

  # Standard year (2025): 365 days
  res_2025 = service.get_year_productivity_grid(year=2025, reference_date=date(2025, 6, 1))
  assert res_2025["year"] == 2025
  assert res_2025["total_days"] == 365
  assert len(res_2025["days"]) == 365
  assert len(res_2025["months"]) == 12

  # Leap year (2024): 366 days
  res_2024 = service.get_year_productivity_grid(year=2024, reference_date=date(2024, 12, 31))
  assert res_2024["year"] == 2024
  assert res_2024["total_days"] == 366
  assert len(res_2024["days"]) == 366


def test_year_productivity_smart_composite_rules(temp_db):
  """Verify Rule 1: Smart composite productivity conditions."""
  log_repo = LogRepository()
  score_repo = ScoreRepository()
  service = LifeCalendarService(birth_date=date(2000, 1, 1), target_age=70)
  ref_date = date(2026, 1, 15)

  # 1. Day with productivity_score >= 50
  d1 = date(2026, 1, 2)
  log_repo.create(DailyLogCreate(date=d1, top_priority="Write spec"))
  score_repo.create(ScoreCreate(date=d1, scope="daily", productivity_score=65.0))

  # 2. Day with deep_work_hours >= 1.5
  d2 = date(2026, 1, 3)
  log_repo.create(DailyLogCreate(date=d2, deep_work_hours=2.0))

  # 3. Day with task_completion_rate >= 0.5 and tasks_completed > 0
  d3 = date(2026, 1, 4)
  log_repo.create(
    DailyLogCreate(
      date=d3,
      task_completion_rate=0.75,
      planned_tasks='[{"text": "Refactor API", "completed": true}]',
    )
  )

  # 4. Day with both morning and evening completed
  d4 = date(2026, 1, 5)
  log_repo.create(
    DailyLogCreate(
      date=d4,
      morning_completed=True,
      evening_completed=True,
    )
  )

  # 5. Day with low execution (not productive)
  d5 = date(2026, 1, 6)
  log_repo.create(
    DailyLogCreate(
      date=d5,
      deep_work_hours=0.5,
      morning_completed=True,
      evening_completed=False,
    )
  )
  score_repo.create(ScoreCreate(date=d5, scope="daily", productivity_score=30.0))

  res = service.get_year_productivity_grid(year=2026, reference_date=ref_date)
  days_map = {d["date"]: d for d in res["days"]}

  assert days_map[d1.isoformat()]["is_productive"] is True
  assert days_map[d2.isoformat()]["is_productive"] is True
  assert days_map[d3.isoformat()]["is_productive"] is True
  assert days_map[d4.isoformat()]["is_productive"] is True
  assert days_map[d5.isoformat()]["is_productive"] is False
  assert days_map[d5.isoformat()]["has_log"] is True

  # Check total productive count
  assert res["productive_days_count"] == 4


def test_year_productivity_streaks(temp_db):
  """Verify streak calculations."""
  log_repo = LogRepository()
  score_repo = ScoreRepository()
  service = LifeCalendarService(birth_date=date(2000, 1, 1), target_age=70)
  ref_date = date(2026, 1, 5)

  # 3 consecutive productive days leading up to ref_date
  for d in [date(2026, 1, 3), date(2026, 1, 4), date(2026, 1, 5)]:
    log_repo.create(DailyLogCreate(date=d, deep_work_hours=2.5))

  res = service.get_year_productivity_grid(year=2026, reference_date=ref_date)
  assert res["productive_days_count"] == 3
  assert res["current_streak"] == 3
  assert res["best_streak"] == 3


def test_api_calendar_year_endpoint(temp_db):
  client = TestClient(app)
  response = client.get("/api/calendar/year?year=2026")
  assert response.status_code == 200
  data = response.json()
  assert data["year"] == 2026
  assert "days" in data
  assert "months" in data
  assert len(data["days"]) == 365
  assert len(data["months"]) == 12
  assert "productive_days_count" in data
  assert "productivity_rate" in data
  assert "current_streak" in data
