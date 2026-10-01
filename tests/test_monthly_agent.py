"""Saved months and yearly pacing as agent context: tools, coach context, and deterministic fallbacks."""

import json
from datetime import date

from ai.pipelines._base import fallback_future_self, fallback_progress
from ai.tools import TOOL_DEFINITIONS, execute_tool, get_scoped_tool_definitions
from database.connection import get_db
from database.repositories.goal_repository import GoalRepository
from database.repositories.log_repository import LogRepository
from database.repositories.monthly_repository import MonthlyRepository
from models.daily_log import DailyLogCreate
from models.goal import GoalCreate
from models.monthly import GoalMeasurementCreate
from services.coach_service import CoachService
from services.monthly_analytics_service import MonthlyAnalyticsService


def _names(domains):
  return {t["function"]["name"] for t in get_scoped_tool_definitions(domains)}


def _log(day: date, done: int, total: int):
  tasks = [{"text": f"t{i}", "completed": i < done} for i in range(total)]
  LogRepository().create(DailyLogCreate(date=day, planned_tasks=json.dumps(tasks), awake_range="8:00 AM - 1:00 AM"))


def _measured_goal():
  goal = GoalRepository().create(GoalCreate(
    title="Getting paid", category="career", horizon="1-year", deadline=date(2026, 12, 31),
    metric_name="Monthly income", metric_unit="INR", start_value=0, target_value=50000,
  ))
  with get_db() as conn:
    conn.execute("UPDATE goals SET created_at = '2026-08-01 08:00:00' WHERE id = ?", (goal.id,))
  MonthlyRepository().upsert_measurement(goal.id, GoalMeasurementCreate(month="2026-09", value=5000))
  return goal


def test_new_tools_live_in_their_own_domains():
  assert "get_goal_pacing" in _names(["goals"]) and "get_goal_pacing" not in _names(["journal"])
  assert "get_monthly_snapshots" in _names(["journal"]) and "get_monthly_snapshots" not in _names(["goals"])
  default_names = {t["function"]["name"] for t in TOOL_DEFINITIONS}
  assert {"get_goal_pacing", "get_monthly_snapshots"} <= default_names


def test_get_goal_pacing_tool_returns_measured_status(temp_db):
  goal = _measured_goal()
  result = execute_tool("get_goal_pacing", {"horizon": "1-year"})
  [entry] = result["goals"]
  assert entry["goal_id"] == goal.id and entry["status"] == "behind" and entry["latest"]["value"] == 5000.0
  assert execute_tool("get_goal_pacing", {"horizon": "bogus"})["error"]


def test_get_monthly_snapshots_tool_returns_compact_saved_months(temp_db):
  _log(date(2026, 8, 31), 1, 2)
  _log(date(2026, 9, 1), 2, 4)
  MonthlyAnalyticsService().recompute_all(today=date(2026, 10, 2))
  both = execute_tool("get_monthly_snapshots", {})
  assert [m["month"] for m in both["months"]] == ["2026-08", "2026-09"]
  sep = both["months"][1]
  assert sep["tasks"]["completion_rate"] == 50.0 and "top_levers" in sep and "focus" in sep
  assert "weekly" not in json.dumps(sep)  # the digest is trimmed for prompt size
  assert [m["month"] for m in execute_tool("get_monthly_snapshots", {"months": 1})["months"]] == ["2026-09"]
  assert len(execute_tool("get_monthly_snapshots", {"months": 99})["months"]) == 2  # capped at 12, not an error


def test_coach_context_carries_saved_months_and_yearly_pacing(temp_db):
  _log(date(2026, 9, 1), 2, 4)
  goal = _measured_goal()
  context = CoachService().build_context(date(2026, 10, 2))
  assert [m["month"] for m in context["monthly_history"]] == ["2026-09"]
  assert [p["goal_id"] for p in context["goal_pacing"]] == [goal.id]


_HISTORY = [
  {"month": "2026-08", "tasks": {"planned": 126, "done": 54, "completion_rate": 42.9}, "top_levers": [], "delta_vs_previous": {}},
  {
    "month": "2026-09", "status": "final",
    "tasks": {"planned": 100, "done": 48, "completion_rate": 48.0},
    "delta_vs_previous": {"completion_rate": 5.1},
    "top_levers": [{"lever": "wake", "tier": "strong", "n": 57, "contrast": "Wake by 07:30: 62% of tasks done (n=18) vs wake 08:30 or later: 37% (n=31)"}],
  },
]
_BEHIND = {
  "goal_id": 1, "title": "Getting paid", "horizon": "1-year", "status": "behind", "metric_unit": "INR",
  "latest": {"month": "2026-09", "value": 5000.0}, "expected_now": 19736.84, "pct_of_target": 10.0,
  "target_value": 50000.0, "deadline": "2026-12-31", "projection": None,
}


def test_progress_fallback_quotes_the_saved_months_and_yearly_pacing():
  context = {"monthly_progress": {"days_logged": 30, "days_in_month": 30}, "month_name": "September 2026",
             "active_goals": [], "recent_logs": [], "monthly_history": _HISTORY, "goal_pacing": [_BEHIND]}
  narrative = fallback_progress(context)["progress_narrative"]
  assert "48.0%" in narrative and "42.9%" in narrative  # this month vs last, from the saved snapshots
  assert "Wake by 07:30" in narrative and "n=57" in narrative
  assert "Getting paid" in narrative and "behind" in narrative.lower() and "5000" in narrative


def test_progress_fallback_unchanged_when_nothing_is_saved():
  context = {"monthly_progress": {"days_logged": 3, "days_in_month": 30}, "active_goals": [], "recent_logs": []}
  assert "saved months" not in fallback_progress(context)["progress_narrative"].lower()


def test_future_self_fallback_uses_measured_pacing_when_it_exists():
  context = {
    "current_age_in_10_years": 34,
    "user_vision": {"five_year_vision": "Networth", "ten_year_vision": "Net worth of 10 crore"},
    "recent_logs": [{"task_completion_rate": 80.0}],
    "goal_pacing": [{
      "goal_id": 2, "title": "Networth", "horizon": "5-year", "status": "behind", "metric_unit": "crore INR",
      "latest": {"month": "2026-09", "value": 2.0}, "expected_now": 2.4, "pct_of_target": 12.0,
      "target_value": 3.0, "deadline": "2030-12-31", "projection": {"value_at_deadline": 2.6, "on_track": False},
    }],
  }
  five = fallback_future_self(context)["five_year_pacing"]
  assert "Networth" in five and "Behind pace" in five and "2.4" in five and "2.6" in five
  assert "On pace" not in five  # the 80% task-completion heuristic must not override a measured gap


def test_future_self_fallback_says_when_a_goal_has_no_measurement():
  context = {
    "current_age_in_10_years": 34,
    "user_vision": {"five_year_vision": "Net worth target", "ten_year_vision": "Financial independence"},
    "recent_logs": [{"task_completion_rate": 20.0}],
  }
  result = fallback_future_self(context)
  assert "Off pace" in result["five_year_pacing"]  # execution read still given
  assert "no numeric check-in" in result["five_year_pacing"].lower()


def _row(title, done_recent, days_quiet, done_30d=None):
  return {"goal_id": 1, "title": title, "horizon": "1-year", "done_recent": done_recent,
          "done_30d": done_recent if done_30d is None else done_30d, "last_done_date": None,
          "days_quiet": days_quiet, "window_days": 14, "as_of": "2026-09-30"}


def test_coach_context_carries_per_goal_attention(temp_db):
  goal = GoalRepository().create(GoalCreate(title="Getting a job", category="career", horizon="1-year", cues=["appl"]))
  LogRepository().create(DailyLogCreate(
    date=date(2026, 9, 30), planned_tasks=json.dumps([{"text": "Apply", "completed": True}]),
  ))
  rows = CoachService().build_context(date(2026, 10, 2))["goal_attention"]
  assert [(r["goal_id"], r["done_recent"]) for r in rows] == [(goal.id, 1)]


def test_progress_fallback_names_the_goals_that_got_work_and_the_quiet_ones():
  context = {"monthly_progress": {"days_logged": 30, "days_in_month": 30}, "active_goals": [], "recent_logs": [],
             "goal_attention": [_row("Getting a job", 6, 0), _row("Getting fit", 0, 21, done_30d=2), _row("Partner", 0, None, 0)]}
  narrative = fallback_progress(context)["progress_narrative"]
  assert "Getting a job 6" in narrative
  assert "Getting fit (21 days)" in narrative and "Partner (never)" in narrative


def test_progress_fallback_does_not_call_unlinked_tasks_neglect():
  context = {"monthly_progress": {"days_logged": 30, "days_in_month": 30}, "active_goals": [], "recent_logs": [],
             "goal_attention": [_row("Getting a job", 0, None, 0), _row("Getting fit", 0, None, 0)]}
  narrative = fallback_progress(context)["progress_narrative"]
  assert "cannot be measured" in narrative and "Quiet" not in narrative
