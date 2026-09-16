"""Tests for the weekly digest report service and the tunable coach persona."""

import os
import sys
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from api.main import app
from services.persona_service import TONE_PRESETS, PersonaService
from services.report_service import ReportService


@pytest.fixture
def client(temp_db):
  return TestClient(app)


def _seed_week(client, week_start: date) -> None:
  for offset in range(3):
    day = week_start + timedelta(days=offset)
    client.post(
      "/api/journal/upsert",
      json={
        "date": day.isoformat(),
        "sleep_hours": 7.0 + offset,
        "deep_work_hours": 3.0,
        "mood_evening": 4,
        "one_win": f"Shipped item {offset}",
        "one_lesson": f"Lesson {offset}",
        "planned_tasks": '[{"text": "task", "priority": 1, "completed": true}]',
      },
    )


# ---------------------------------------------------------------------------
# Report Service
# ---------------------------------------------------------------------------


def test_build_report_aggregates_week(client):
  week_start = date.today() - timedelta(days=6)
  _seed_week(client, week_start)

  report = ReportService().build_report(week_start)

  assert report["week_start"] == week_start.isoformat()
  assert report["week_end"] == (week_start + timedelta(days=6)).isoformat()
  assert report["days_logged"] == 3
  assert report["averages"]["sleep_hours"] == 8.0
  assert report["averages"]["deep_work_hours"] == 3.0
  assert len(report["takeaways"]) == 6  # one win + one lesson per seeded day


def test_build_report_handles_empty_week(temp_db):
  report = ReportService().build_report(date(2001, 1, 1))
  assert report["days_logged"] == 0
  assert report["averages"]["sleep_hours"] is None
  assert report["takeaways"] == []


def test_render_markdown_and_html(temp_db):
  service = ReportService()
  report = service.build_report(date(2001, 1, 1))

  markdown = service.render_markdown(report)
  assert markdown.startswith("# GoalOS Weekly Digest")
  assert "## Daily Breakdown" in markdown
  assert "No wins or lessons recorded this week." in markdown

  page = service.render_html(report)
  assert page.startswith("<!doctype html>")
  assert "GoalOS Weekly Digest" in page


def test_weekly_report_endpoint_markdown(client):
  week_start = date.today() - timedelta(days=6)
  _seed_week(client, week_start)

  response = client.get(f"/api/export/weekly-report?week_start_date={week_start.isoformat()}")
  assert response.status_code == 200
  assert response.headers["content-type"].startswith("text/markdown")
  assert "GoalOS Weekly Digest" in response.text


def test_weekly_report_endpoint_html_and_json(client):
  week_start = date.today() - timedelta(days=6)

  html_res = client.get(f"/api/export/weekly-report?week_start_date={week_start.isoformat()}&format=html")
  assert html_res.status_code == 200
  assert html_res.headers["content-type"].startswith("text/html")

  json_res = client.get(f"/api/export/weekly-report?week_start_date={week_start.isoformat()}&format=json")
  assert json_res.status_code == 200
  assert json_res.json()["week_start"] == week_start.isoformat()


def test_weekly_report_rejects_bad_date(client):
  assert client.get("/api/export/weekly-report?week_start_date=not-a-date").status_code == 400


def test_weekly_report_available_on_legacy_root(client):
  assert client.get("/export/weekly-report").status_code == 200


# ---------------------------------------------------------------------------
# Coach Persona
# ---------------------------------------------------------------------------


def test_persona_defaults_to_no_directives(temp_db):
  assert PersonaService().build_directives() == ""


def test_settings_roundtrip_persona_fields(client):
  response = client.post(
    "/api/settings",
    json={"preferred_tone": "socratic_inquirer", "custom_coach_prompt": "Always name the avoided task."},
  )
  assert response.status_code == 200
  data = response.json()
  assert data["preferred_tone"] == "socratic_inquirer"
  assert data["custom_coach_prompt"] == "Always name the avoided task."


def test_persona_directives_render_tone_and_custom_prompt(client):
  client.post(
    "/api/settings",
    json={"preferred_tone": "direct_accountability", "custom_coach_prompt": "No cliches."},
  )
  directives = PersonaService().build_directives()

  assert "PERSONA DIRECTIVES" in directives
  assert TONE_PRESETS["direct_accountability"] in directives
  assert "No cliches." in directives


def test_persona_ignores_unknown_tone(client):
  client.post("/api/settings", json={"preferred_tone": "pirate_captain"})
  assert PersonaService().build_directives() == ""


def test_coordinator_prompt_carries_persona(client):
  from ai.pipelines.coordinator import CoordinatorPipeline

  client.post("/api/settings", json={"preferred_tone": "executive_mentor"})
  prompt = CoordinatorPipeline()._build_system_prompt("goals", {}, [])

  assert "PERSONA DIRECTIVES" in prompt
  assert TONE_PRESETS["executive_mentor"] in prompt


# ---------------------------------------------------------------------------
# Telemetry endpoints (APM dashboard backing)
# ---------------------------------------------------------------------------


def test_telemetry_summary_shape(client):
  response = client.get("/api/coach/telemetry/summary")
  assert response.status_code == 200
  data = response.json()
  for field in ("total_calls", "prompt_tokens", "completion_tokens", "total_cost_usd", "avg_latency_ms", "p95_latency_ms"):
    assert field in data


def test_telemetry_traces_shape(client):
  response = client.get("/api/coach/telemetry/traces?limit=5")
  assert response.status_code == 200
  assert isinstance(response.json(), list)
