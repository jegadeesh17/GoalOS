"""Unit tests for Life Calendar Service, Weekly Sync Service, and July Journal Folder Scanner."""

import os
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


def test_july_journal_folder_scan_and_grouping():
  sync = WeeklySyncService()
  july_folder = r"c:\Users\jegad\projects\GoalOS\data\July Journal"
  assert os.path.exists(july_folder)

  entries = sync.scan_journal_folder(july_folder, start_date=date(2026, 7, 1))
  assert len(entries) == 31  # 31 days in July

  weeks = sync.group_entries_into_weeks(entries)
  assert len(weeks) == 5  # 4 full 7-day weeks + 1 remaining 3-day week

  weekly_reports = [sync.generate_weekly_report(w["entries"], active_goals=[]) for w in weeks]
  assert len(weekly_reports) == 5

  monthly_summary = sync.generate_monthly_summary(weekly_reports, "July 2026")
  assert monthly_summary["total_days_logged"] == 31
  assert monthly_summary["total_weeks"] == 5
