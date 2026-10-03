"""Yearly goal pacing against measurable targets and monthly check-ins."""

import os
import sys
from datetime import date

import pytest
from fastapi.testclient import TestClient

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from api.main import app
from database.connection import get_db
from database.repositories.goal_repository import GoalRepository
from database.repositories.monthly_repository import MonthlyRepository
from models.goal import GoalCreate
from models.monthly import GoalMeasurementCreate, GoalPacePointCreate
from services.yearly_pacing_service import YearlyPacingService

TODAY = date(2026, 10, 2)


def _goal(created: str = "2026-08-01 08:00:00", **fields):
  defaults = {"title": "Applications", "category": "career", "horizon": "1-year", "deadline": date(2026, 12, 31)}
  goal = GoalRepository().create(GoalCreate(**{**defaults, **fields}))
  with get_db() as conn:
    conn.execute("UPDATE goals SET created_at = ? WHERE id = ?", (created, goal.id))
  return goal


def _check_in(goal_id: int, month: str, value: float):
  MonthlyRepository().upsert_measurement(goal_id, GoalMeasurementCreate(month=month, value=value))


def _pace(goal_id: int):
  [result] = [r for r in YearlyPacingService().evaluate_all(today=TODAY) if r["goal_id"] == goal_id]
  return result


def test_worked_example_behind_pace_with_one_check_in(temp_db):
  goal = _goal(metric_name="Applications sent", start_value=0, target_value=120)
  _check_in(goal.id, "2026-09", 25)
  r = _pace(goal.id)
  assert r["status"] == "behind"
  assert r["latest"] == {"month": "2026-09", "value": 25.0}
  assert r["expected_now"] == 47.37 and r["gap"] == -22.37 and r["pct_of_target"] == 20.8
  assert r["projection"] is None  # one check-in is not a trend


def test_ahead_and_on_pace_use_a_ten_percent_band(temp_db):
  ahead = _goal(title="A", start_value=0, target_value=120)
  steady = _goal(title="B", start_value=0, target_value=120)
  _check_in(ahead.id, "2026-09", 60)  # +12.6 vs a 12 band
  _check_in(steady.id, "2026-09", 50)  # +2.6
  assert _pace(ahead.id)["status"] == "ahead"
  assert _pace(steady.id)["status"] == "on_pace"


def test_goal_that_should_go_down_is_judged_in_its_own_direction(temp_db):
  goal = _goal(title="Weight", start_value=85, target_value=75, created="2026-01-01 08:00:00")
  _check_in(goal.id, "2026-06", 80)
  r = _pace(goal.id)
  assert r["status"] == "on_pace" and r["pct_of_target"] == 50.0
  _check_in(goal.id, "2026-06", 84)
  assert _pace(goal.id)["status"] == "behind"


def test_without_a_start_value_the_first_check_in_is_the_baseline(temp_db):
  goal = _goal(title="Net worth", start_value=None, target_value=100, deadline=date(2036, 12, 31), horizon="10-year")
  assert _pace(goal.id)["status"] == "no_check_ins"
  _check_in(goal.id, "2026-09", 2)
  r = _pace(goal.id)
  assert r["status"] == "baseline_only" and r["baseline"]["source"] == "first_check_in"
  _check_in(goal.id, "2026-10", 2.5)
  r = _pace(goal.id)
  assert r["baseline"] == {"value": 2.0, "source": "first_check_in", "date": "2026-09-30"}
  assert r["status"] in {"ahead", "on_pace", "behind"} and r["latest"]["month"] == "2026-10"


def test_projection_needs_three_check_ins_and_says_whether_the_target_is_reachable(temp_db):
  goal = _goal(start_value=0, target_value=120)
  for month, value in (("2026-09", 20), ("2026-10", 40), ("2026-11", 60)):
    _check_in(goal.id, month, value)
  r = _pace(goal.id)
  assert r["check_ins"] == 3
  assert 75 < r["projection"]["value_at_deadline"] < 85 and r["projection"]["on_track"] is False


def test_goals_without_numbers_are_reported_honestly(temp_db):
  qualitative = _goal(title="Partner", horizon="5-year")
  no_check_ins = _goal(title="Income", start_value=0, target_value=50000)
  no_deadline = _goal(title="Weight", start_value=85, target_value=75, deadline=None)
  _check_in(no_deadline.id, "2026-09", 83)
  assert _pace(qualitative.id)["status"] == "qualitative"
  assert _pace(no_check_ins.id)["status"] == "no_check_ins"
  assert _pace(no_deadline.id)["status"] == "no_deadline"


def test_horizon_filter_and_inactive_goals(temp_db):
  year = _goal(title="Year", horizon="1-year", target_value=10, start_value=0)
  five = _goal(title="Five", horizon="5-year")
  month = _goal(title="Month", horizon="1-month")
  done = _goal(title="Done", horizon="1-year", status="completed")
  svc = YearlyPacingService()
  ids = {r["goal_id"] for r in svc.evaluate_all(today=TODAY)}
  assert {year.id, five.id} <= ids and month.id not in ids and done.id not in ids  # default: yearly and beyond
  only_five = {r["goal_id"] for r in svc.evaluate_all(horizon="5-year", today=TODAY)}
  assert only_five == {five.id}


@pytest.fixture
def client(temp_db):
  return TestClient(app)


def test_goal_target_fields_round_trip_through_the_api(client):
  created = client.post("/goals", json={
    "title": "Net worth", "category": "finance", "horizon": "10-year", "deadline": "2036-12-31",
    "metric_name": "Net worth", "metric_unit": "crore INR", "target_value": 25,
  }).json()
  assert (created["metric_name"], created["metric_unit"], created["target_value"]) == ("Net worth", "crore INR", 25.0)
  updated = client.put(f"/goals/{created['id']}", json={"start_value": 2.0}).json()
  assert updated["start_value"] == 2.0 and updated["target_value"] == 25.0


def test_check_in_endpoints_and_pacing_listing(client):
  goal = client.post("/goals", json={
    "title": "Applications", "category": "career", "horizon": "1-year", "deadline": "2026-12-31",
    "start_value": 0, "target_value": 120,
  }).json()
  put = client.put(f"/goals/{goal['id']}/measurements", json={"month": "2026-09", "value": 25, "note": "sent 25"})
  assert put.status_code == 200 and put.json()["value"] == 25.0
  assert client.put(f"/goals/{goal['id']}/measurements", json={"month": "2026-09", "value": 30}).json()["value"] == 30.0
  listing = client.get(f"/goals/{goal['id']}/measurements").json()
  assert [(m["month"], m["value"]) for m in listing] == [("2026-09", 30.0)]
  pacing = client.get("/goals/pacing").json()
  assert [p["goal_id"] for p in pacing] == [goal["id"]] and pacing[0]["latest"]["value"] == 30.0
  assert client.delete(f"/goals/{goal['id']}/measurements/2026-09").status_code == 200
  assert client.delete(f"/goals/{goal['id']}/measurements/2026-09").status_code == 404
  assert client.put("/goals/9999/measurements", json={"month": "2026-09", "value": 1}).status_code == 404
  assert client.put(f"/goals/{goal['id']}/measurements", json={"month": "2026-9", "value": 1}).status_code == 422


# ---- user-written expected path (pace points)


def _point(goal_id: int, due: str, value: float):
  MonthlyRepository().upsert_pace_point(goal_id, GoalPacePointCreate(due=date.fromisoformat(due), value=value))


def test_no_pace_points_is_the_straight_line(temp_db):
  goal = _goal(start_value=0, target_value=120)
  _check_in(goal.id, "2026-09", 25)
  assert _pace(goal.id)["path"] == "linear"


def test_pace_points_replace_the_straight_line_and_scale_the_band_to_the_segment(temp_db):
  # Start 0 on 2026-08-01, expected 10 by 2026-09-30, target 120 on 2026-12-31.
  goal = _goal(start_value=0, target_value=120)
  _point(goal.id, "2026-09-30", 10)
  _check_in(goal.id, "2026-09", 12)
  r = _pace(goal.id)
  assert r["path"] == "custom"
  assert r["expected_now"] == 10.0 and r["gap"] == 2.0
  assert r["status"] == "ahead"  # +2 against a band of 1 (10% of the 0-10 segment), not of the whole 120
  assert r["projection"] is None  # a straight-line trend says nothing about a back-loaded path


def test_custom_path_still_reports_behind_and_on_pace(temp_db):
  behind = _goal(title="A", start_value=0, target_value=120)
  steady = _goal(title="B", start_value=0, target_value=120)
  for g in (behind, steady):
    _point(g.id, "2026-09-30", 10)
  _check_in(behind.id, "2026-09", 8)
  _check_in(steady.id, "2026-09", 10.5)
  assert _pace(behind.id)["status"] == "behind"
  assert _pace(steady.id)["status"] == "on_pace"


def test_expected_value_is_interpolated_between_the_users_points(temp_db):
  goal = _goal(start_value=0, target_value=120)
  _point(goal.id, "2026-09-30", 10)
  _check_in(goal.id, "2026-08", 5)  # 2026-08-31 is 30 of the 60 days to the first point
  assert _pace(goal.id)["expected_now"] == 5.0


def test_pace_points_outside_the_goal_span_are_ignored(temp_db):
  goal = _goal(start_value=0, target_value=120)
  _point(goal.id, "2027-06-01", 5)  # after the deadline
  _point(goal.id, "2026-01-01", 99)  # before the start
  _check_in(goal.id, "2026-09", 25)
  r = _pace(goal.id)
  assert r["path"] == "linear" and r["expected_now"] == 47.37


def test_pace_point_endpoints_and_migration(client):
  goal = client.post("/goals", json={
    "title": "Net worth", "category": "finance", "horizon": "10-year", "deadline": "2036-12-31",
    "start_value": 0, "target_value": 100,
  }).json()
  base = f"/goals/{goal['id']}/pace-points"
  assert client.put(base, json={"due": "2027-12-31", "value": 2}).status_code == 200
  assert client.put(base, json={"due": "2027-12-31", "value": 3}).json()["value"] == 3.0
  assert client.put(base, json={"due": "2031-12-31", "value": 30}).status_code == 200
  assert [(p["due"], p["value"]) for p in client.get(base).json()] == [("2027-12-31", 3.0), ("2031-12-31", 30.0)]
  assert client.delete(f"{base}/2027-12-31").status_code == 200
  assert client.delete(f"{base}/2027-12-31").status_code == 404
  assert client.delete(f"{base}/not-a-date").status_code == 422
  assert client.put("/goals/9999/pace-points", json={"due": "2027-12-31", "value": 1}).status_code == 404
  assert client.put(base, json={"due": "soon", "value": 1}).status_code == 422
  with get_db() as conn:
    conn.execute("DELETE FROM goals WHERE id = ?", (goal["id"],))
    left = conn.execute("SELECT COUNT(*) FROM goal_pace_points WHERE goal_id = ?", (goal["id"],)).fetchone()[0]
  assert left == 0  # points go with their goal


def test_coach_line_says_when_pace_is_judged_on_the_users_own_path(temp_db):
  from ai.pipelines._base import _measured_line

  goal = _goal(start_value=0, target_value=120, title="Net worth")
  _check_in(goal.id, "2026-09", 12)
  assert "expected by then" in _measured_line(_pace(goal.id))
  _point(goal.id, "2026-09-30", 10)
  assert "on the path they wrote for it by then" in _measured_line(_pace(goal.id))
