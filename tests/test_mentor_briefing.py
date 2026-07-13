"""Tests for personalized mentor briefing."""

from datetime import date

from services.mentor_briefing import build_mentor_briefing, personalized_fallback_rule


def test_fallback_uses_review_quote():
  briefing = {
    "top_priority_task": "Solve 10 codekata",
    "one_year_goal": "Get placed by June",
    "most_recent_review": {
      "date": "2026-06-24",
      "text": "No work, wasted time scrolling. Time once gone cannot be bought.",
    },
    "repeated_incomplete_tasks": [],
    "most_recent_takeaway": "",
    "avg_task_completion_7d": 35.0,
  }
  result = personalized_fallback_rule(briefing)
  assert "codekata" in result["mentor_rule"].lower()
  assert "2026-06-24" in result["why_this_rule"] or "scrolling" in result["why_this_rule"].lower()
  assert result["source"] == "personalized_fallback"


def test_fallback_uses_repeated_task():
  briefing = {
    "top_priority_task": "Finish evaluation",
    "one_year_goal": "Software job",
    "most_recent_review": None,
    "repeated_incomplete_tasks": [{"task": "solve 10 codekata", "times_incomplete": 4}],
    "most_recent_takeaway": "",
    "avg_task_completion_7d": 20.0,
  }
  result = personalized_fallback_rule(briefing)
  assert "codekata" in result["why_this_rule"].lower()
  assert "evaluation" in result["mentor_rule"].lower()


def test_briefing_extracts_today_tasks():
  today = date(2026, 6, 26)
  today_log = {
    "date": today.isoformat(),
    "planned_tasks": '[{"text": "Task A", "priority": 1, "completed": false}, {"text": "Task B", "priority": 2, "completed": false}]',
  }
  briefing = build_mentor_briefing(today, today_log, [], {"one_year_vision": "Get a job"})
  assert briefing["top_priority_task"] == "Task A"
  assert briefing["one_year_goal"] == "Get a job"
