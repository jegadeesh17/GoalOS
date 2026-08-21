"""Unit tests for PatternService and pattern-focused AI coaching."""

from datetime import date

from services.mentor_briefing import build_mentor_briefing, personalized_fallback_rule
from services.pattern_service import PatternService


def test_isolated_one_day_friction_is_not_marked_chronic():
  service = PatternService()
  logs = [
    {
      "date": "2026-07-01",
      "journal_entry": "Distracted by phone today, did not finish task.",
      "takeaway": "Put phone in other room.",
      "planned_tasks": '[{"text": "Deep work codekata", "priority": 1, "completed": false}]',
    },
    {
      "date": "2026-07-02",
      "journal_entry": "Great day, deep work finished early.",
      "takeaway": "Morning momentum was key.",
      "planned_tasks": '[{"text": "Deep work codekata", "priority": 1, "completed": true}]',
    },
    {
      "date": "2026-07-03",
      "journal_entry": "Solid progress on project.",
      "takeaway": "Keep going.",
      "planned_tasks": '[{"text": "Project setup", "priority": 1, "completed": true}]',
    },
  ]

  report = service.analyze_patterns(logs, target_date=date(2026, 7, 4))
  assert report["has_chronic_patterns"] is False
  assert len(report["repeating_unhealthy_patterns"]) == 0
  assert len(report["isolated_friction_events"]) >= 1
  assert any("phone" in event["category"] for event in report["isolated_friction_events"])


def test_repeating_unhealthy_pattern_detected_with_dates_and_triggers():
  service = PatternService()
  logs = [
    {
      "date": "2026-07-01",
      "journal_entry": "Wasted time scrolling phone in bed.",
      "takeaway": "Stop phone scrolling.",
    },
    {
      "date": "2026-07-03",
      "journal_entry": "Phone scrolling delayed morning start again.",
      "takeaway": "Need phone boundary.",
    },
    {
      "date": "2026-07-05",
      "journal_entry": "Solid morning execution.",
      "takeaway": "Good focus.",
    },
  ]

  report = service.analyze_patterns(logs, target_date=date(2026, 7, 6))
  assert report["has_chronic_patterns"] is True
  assert len(report["repeating_unhealthy_patterns"]) >= 1

  primary = report["primary_unhealthy_loop"]
  assert primary is not None
  assert primary["category"] == "phone"
  assert primary["occurrences_count"] == 2
  assert "2026-07-01" in primary["dates_observed"]
  assert "2026-07-03" in primary["dates_observed"]
  assert len(primary["actionable_countermeasure"]) > 10


def test_task_rollover_pattern_detected():
  service = PatternService()
  logs = [
    {
      "date": "2026-07-01",
      "planned_tasks": '[{"text": "Solve 10 LeetCode problems", "priority": 1, "completed": false}]',
    },
    {
      "date": "2026-07-02",
      "planned_tasks": '[{"text": "Solve 10 LeetCode problems", "priority": 1, "completed": false}]',
    },
    {
      "date": "2026-07-03",
      "planned_tasks": '[{"text": "Solve 10 LeetCode problems", "priority": 1, "completed": false}]',
    },
  ]

  report = service.analyze_patterns(logs, target_date=date(2026, 7, 4))
  rollover_patterns = [p for p in report["repeating_unhealthy_patterns"] if p["category"] == "task_rollover"]
  assert len(rollover_patterns) == 1
  assert rollover_patterns[0]["occurrences_count"] == 3
  assert rollover_patterns[0]["severity"] == "critical"


def test_mentor_briefing_prioritizes_repeating_patterns():
  today = date(2026, 7, 6)
  today_log = {
    "date": today.isoformat(),
    "planned_tasks": '[{"text": "Finish MVP architecture", "priority": 1, "completed": false}]',
  }
  recent_logs = [
    {
      "date": "2026-07-02",
      "journal_entry": "Lost 2 hours to youtube videos during work hours.",
      "takeaway": "Close browser tabs.",
    },
    {
      "date": "2026-07-04",
      "journal_entry": "Youtube video binging in the afternoon again.",
      "takeaway": "Block entertainment sites.",
    },
  ]

  briefing = build_mentor_briefing(today, today_log, recent_logs, {"one_year_vision": "Senior Engineer Placement"})
  assert len(briefing["recognized_patterns"]) >= 1
  assert briefing["primary_unhealthy_loop"]["category"] == "entertainment"

  rule_result = personalized_fallback_rule(briefing)
  assert "MVP architecture" in rule_result["mentor_rule"] or "loop" in rule_result["mentor_rule"].lower() or "entertainment" in rule_result["past_mistake_called_out"].lower()
  assert "2026-07-02" in rule_result["why_this_rule"] or "2026-07-04" in rule_result["why_this_rule"]
