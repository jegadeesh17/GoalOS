"""Test suite for expanded GoalOS REST endpoints."""

import os
import sys
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from api.main import app


@pytest.fixture
def client(temp_db):
  return TestClient(app)


def test_calendar_summary(client):
  response = client.get("/calendar/summary")
  assert response.status_code == 200
  data = response.json()
  assert "total_weeks" in data
  assert "weeks_lived" in data
  assert "weeks_remaining" in data
  assert "percentage_lived" in data
  assert data["total_weeks"] > 0


def test_calendar_grid(client):
  response = client.get("/calendar/grid")
  assert response.status_code == 200
  grid = response.json()
  assert len(grid) == 70
  assert len(grid[0]["weeks"]) == 52


def test_goals_crud(client):
  # 1. Create Goal
  create_res = client.post(
    "/goals",
    json={
      "title": "Build AI Agent OS",
      "category": "Career",
      "horizon": "1-year",
      "priority": 1,
      "reason": "Master AI agents",
    },
  )
  assert create_res.status_code == 200
  goal = create_res.json()
  assert goal["title"] == "Build AI Agent OS"
  goal_id = goal["id"]

  # 2. Get Goals & Horizons
  horizons_res = client.get("/goals/horizons")
  assert horizons_res.status_code == 200
  horizons = horizons_res.json()
  assert "1-year" in horizons
  assert any(g["id"] == goal_id for g in horizons["1-year"])

  # 3. Add Milestone
  ms_res = client.post(
    f"/goals/{goal_id}/milestones",
    json={"goal_id": goal_id, "title": "Launch Alpha", "status": "active"},
  )
  assert ms_res.status_code == 200
  ms = ms_res.json()
  assert ms["title"] == "Launch Alpha"
  ms_id = ms["id"]

  # Update Milestone
  patch_ms = client.patch(
    f"/milestones/{ms_id}",
    json={"status": "completed", "progress": 1.0},
  )
  assert patch_ms.status_code == 200
  assert patch_ms.json()["status"] == "completed"

  # 4. Get Goal by ID
  get_res = client.get(f"/goals/{goal_id}")
  assert get_res.status_code == 200
  assert len(get_res.json()["milestones"]) == 1

  # 5. Delete Goal
  del_res = client.delete(f"/goals/{goal_id}")
  assert del_res.status_code == 200
  assert del_res.json()["success"] is True


def test_journal_upsert_and_today(client):
  today = date.today().isoformat()
  res = client.post(
    "/journal/upsert",
    json={
      "date": today,
      "sleep_hours": 7.5,
      "sleep_quality": 4,
      "mood_morning": 5,
      "intention": "Ship modern Light Mode React UI",
      "deep_work_hours": 4.0,
    },
  )
  assert res.status_code == 200
  data = res.json()
  assert data["sleep_hours"] == 7.5
  assert data["intention"] == "Ship modern Light Mode React UI"

  # Get today
  today_res = client.get("/journal/today")
  assert today_res.status_code == 200
  assert today_res.json()["sleep_hours"] == 7.5

  # Get history
  history_res = client.get("/journal/history?limit=7")
  assert history_res.status_code == 200
  assert isinstance(history_res.json(), list)


def test_analytics_endpoints(client):
  dashboard_res = client.get("/analytics/dashboard")
  assert dashboard_res.status_code == 200
  dashboard = dashboard_res.json()
  assert "total_logs" in dashboard
  assert "avg_sleep_hours" in dashboard
  assert "avg_deep_work_hours" in dashboard

  scores_res = client.get("/analytics/scores?limit=10")
  assert scores_res.status_code == 200
  assert isinstance(scores_res.json(), list)


def test_memories_crud_and_search(client):
  # Create Memory
  create_res = client.post(
    "/memories",
    json={
      "text": "Consistency beats intensity every single time",
      "memory_type": "principle",
      "importance": 0.9,
    },
  )
  assert create_res.status_code == 200
  mem = create_res.json()
  assert mem["text"] == "Consistency beats intensity every single time"
  mem_id = mem["id"]

  # List Memories
  list_res = client.get("/memories?limit=20")
  assert list_res.status_code == 200
  assert any(m["id"] == mem_id for m in list_res.json())

  # Search Memories
  search_res = client.get("/memories/search?q=consistency")
  assert search_res.status_code == 200
  assert isinstance(search_res.json(), list)

  # Delete Memory
  del_res = client.delete(f"/memories/{mem_id}")
  assert del_res.status_code == 200
  assert del_res.json()["success"] is True


def test_settings_and_export(client):
  # Get Settings
  get_res = client.get("/settings")
  assert get_res.status_code == 200
  settings_data = get_res.json()
  assert "remote_ai_consent" in settings_data

  # Update Settings
  up_res = client.post(
    "/settings",
    json={
      "target_age": 75,
      "remote_ai_consent": True,
    },
  )
  assert up_res.status_code == 200
  updated = up_res.json()
  assert updated["target_age"] == 75

  # Export payload
  export_res = client.get("/export")
  assert export_res.status_code == 200
  export_data = export_res.json()
  assert "tables" in export_data
  assert "format" in export_data



def test_ai_coach_endpoints(client):
  today = date.today().isoformat()

  # Morning Coach
  morning_res = client.post(
    "/coach/morning",
    json={
      "target_date": today,
      "plans_text": "Ship v2 release",
      "gratitude": "Good health",
    },
  )
  assert morning_res.status_code == 200
  assert "mentor_rule" in morning_res.json() or "rule" in morning_res.json()

  # Evening Coach
  evening_res = client.post(
    "/coach/evening",
    json={
      "target_date": today,
      "one_win": "Everything tested",
      "one_lesson": "Stay focused",
    },
  )
  assert evening_res.status_code == 200

  # Weekly Coach
  weekly_res = client.post("/coach/weekly", json={"week_start_date": today})
  assert weekly_res.status_code == 200

  # Future Self Coach
  future_res = client.post("/coach/future-self", json={"date": today})
  assert future_res.status_code == 200
