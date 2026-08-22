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


def test_settings_get_and_update(client):
  get_res = client.get("/settings")
  assert get_res.status_code == 200
  settings_data = get_res.json()
  assert "remote_ai_consent" in settings_data

  # Update settings
  up_res = client.post(
    "/settings",
    json={
      "target_age": 80,
      "remote_ai_consent": True,
    },
  )
  assert up_res.status_code == 200
  updated = up_res.json()
  assert updated["target_age"] == 80
  assert updated["remote_ai_consent"] is True
