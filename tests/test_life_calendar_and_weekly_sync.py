"""Unit tests for Life Calendar Service and Weekly Sync Service."""

from datetime import date
from services.life_calendar_service import LifeCalendarService
from services.weekly_sync_service import WeeklySyncService


def test_life_calendar_calculations():
  birth = date(2002, 6, 17)
  service = LifeCalendarService(birth_date=birth, target_age=70)
  ref_date = date(2026, 8, 1)

  summary = service.get_summary(reference_date=ref_date)
  assert summary["target_age"] == 70
  assert summary["total_weeks"] == 3640
  assert summary["weeks_lived"] > 0
  assert summary["weeks_remaining"] > 0
  assert summary["weeks_lived"] + summary["weeks_remaining"] == 3640
  assert summary["percentage_lived"] > 0.0

  grid = service.get_grid_data(reference_date=ref_date)
  assert len(grid) == 70
  assert len(grid[0]["weeks"]) == 52


def test_weekly_sync_csv_parser():
  sync = WeeklySyncService()
  sample_csv = """date,gratitude,tasks,wins,review,takeaway
2026-07-27,Morning focus,Task A,Completed task,Felt great,Pace yourself
2026-07-28,Good sleep,Task B,Finished spec,Good progress,Plan early
"""
  entries = sync.parse_csv(sample_csv)
  assert len(entries) == 2
  assert entries[0]["date"] == "2026-07-27"
  assert entries[0]["wins"] == "Completed task"
  assert entries[1]["takeaway"] == "Plan early"


def test_weekly_report_generation():
  sync = WeeklySyncService()
  entries = [
    {"date": "2026-07-27", "wins": "Completed task", "takeaway": "Pace yourself", "review": "Good work"},
    {"date": "2026-07-28", "wins": "Finished spec", "takeaway": "Plan early", "review": "High focus"},
  ]
  report = sync.generate_weekly_report(entries, active_goals=[])
  assert report["total_days_logged"] == 2
  assert "Completed task" in report["wins"]
  assert "Pace yourself" in report["lessons"]
  assert report["goal_alignment_score"] > 0.0
