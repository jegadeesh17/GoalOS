"""Unit tests for Life Calendar Service, Monthly Progress Service, and July Journal Folder Scanner."""

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


def test_july_journal_folder_scan_and_monthly_progress(temp_db):
  sync = WeeklySyncService()
  july_folder = r"c:\Users\jegad\projects\GoalOS\data\Journal"
  if not os.path.exists(july_folder):
    import pytest
    pytest.skip("Local raw journal folder not present in CI environment")

  entries = sync.scan_journal_folder(july_folder, start_date=date(2026, 7, 1))
  assert len(entries) == 31  # 31 days in July

  progress = sync.calculate_monthly_progress(entries, month_start=date(2026, 7, 1), month_name="July 2026")
  assert progress["days_logged"] == 31
  assert progress["days_in_month"] == 31
  assert progress["logging_consistency_rate"] == 100.0
  assert progress["monthly_completion_rate"] > 0.0
  assert progress["is_month_complete"] is True

  monthly_summary = sync.generate_monthly_report(entries, "July 2026")
  assert monthly_summary["total_days_logged"] == 31
  assert monthly_summary["average_goal_alignment"] > 0.0

  yearly_report = sync.generate_yearly_report([monthly_summary], "2026")
  assert yearly_report["total_months"] == 1
  assert yearly_report["total_days_logged"] == 31


def test_monthly_progress_alignment_comes_from_task_links_and_is_never_guessed(temp_db):
  import json

  from database.repositories.goal_repository import GoalRepository
  from database.repositories.log_repository import LogRepository
  from models.daily_log import DailyLogCreate
  from models.goal import GoalCreate

  tasks = [{"text": "Apply", "completed": True}, {"text": "Wash clothes", "completed": True}]
  for day in range(1, 6):
    LogRepository().create(DailyLogCreate(date=date(2026, 9, day), planned_tasks=json.dumps(tasks)))
  entries = [{"date": date(2026, 9, day), "task_completion_rate": 100.0} for day in range(1, 6)]
  sync = WeeklySyncService()

  unlinked = sync.calculate_monthly_progress(entries, month_start=date(2026, 9, 1))
  assert unlinked["semantic_goal_alignment"] is None  # nothing reviewed yet: unknown, not 50
  assert unlinked["monthly_completion_rate"] == 58.4  # logging 16.7% and execution 100%, weights renormalised

  GoalRepository().create(GoalCreate(title="Job", category="career", horizon="1-month", cues=["appl"]))
  assert sync.calculate_monthly_progress(entries, month_start=date(2026, 9, 1))["semantic_goal_alignment"] == 100.0
