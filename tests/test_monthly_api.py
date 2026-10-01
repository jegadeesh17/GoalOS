"""REST surface for stored monthly analytics."""

import json
import os
import sys
from datetime import date

import pytest
from fastapi.testclient import TestClient

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from api.main import app
from database.repositories.log_repository import LogRepository
from models.daily_log import DailyLogCreate


@pytest.fixture
def client(temp_db):
  return TestClient(app)


def _log(day: date, done: int = 1, total: int = 2):
  tasks = [{"text": f"t{i}", "completed": i < done} for i in range(total)]
  LogRepository().create(DailyLogCreate(date=day, planned_tasks=json.dumps(tasks)))


def test_monthly_list_is_built_on_first_read_when_nothing_is_stored(client):
  _log(date(2026, 9, 1))
  body = client.get("/analytics/monthly").json()
  assert [s["month"] for s in body] == ["2026-09"]
  snap = body[0]
  assert snap["status"] == "provisional" and snap["metrics"]["days_logged"] == 1
  assert {"insights", "goal_results", "data_through"} <= set(snap)


def test_single_month_and_validation(client):
  _log(date(2026, 9, 1))
  client.post("/analytics/monthly/recompute")
  assert client.get("/analytics/monthly/2026-09").json()["metrics"]["tasks"]["planned"] == 2
  assert client.get("/analytics/monthly/2026-08").status_code == 404
  assert client.get("/analytics/monthly/2026-13").status_code == 422
  assert client.get("/analytics/monthly/not-a-month").status_code == 422


def test_recompute_one_month_or_all(client):
  _log(date(2026, 8, 31))
  _log(date(2026, 9, 1))
  assert client.post("/analytics/monthly/recompute").json() == {"recomputed": ["2026-08", "2026-09"]}
  assert client.post("/analytics/monthly/recompute", params={"month": "2026-09"}).json()["month"] == "2026-09"
  assert client.post("/analytics/monthly/recompute", params={"month": "2026-05"}).status_code == 404


def test_api_prefix_is_served_too(client):
  _log(date(2026, 9, 1))
  assert client.get("/api/analytics/monthly").status_code == 200


def test_saving_a_journal_day_refreshes_that_months_snapshot(client):
  _log(date(2026, 9, 1))
  assert client.get("/analytics/monthly").json()[0]["metrics"]["days_logged"] == 1  # stored now
  client.post("/journal/upsert", json={"date": "2026-09-15", "planned_tasks": json.dumps([{"text": "a", "completed": True}])})
  assert client.get("/analytics/monthly").json()[0]["metrics"]["days_logged"] == 2  # trigger, not a lazy rebuild
