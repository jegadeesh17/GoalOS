"""Regression tests for vNext integrity, privacy, and lifecycle behavior."""

from datetime import date

from database.repositories.goal_repository import GoalRepository
from database.repositories.log_repository import LogRepository
from database.repositories.milestone_repository import MilestoneRepository
from database.repositories.score_repository import ScoreRepository
from database.repositories.weekly_review_repository import WeeklyReviewRepository
from models.daily_log import DailyLogCreate, DailyLogUpdate
from models.goal import GoalCreate
from models.milestone import MilestoneCreate
from models.score import ScoreCreate
from models.weekly_review import WeeklyReviewCreate
from services.data_portability_service import DataPortabilityService
from services.journal_helpers import serialize_journal_fields
from services.memory_service import MemoryService
from services.settings_service import SettingsService


def test_partial_log_update_preserves_evening_fields(temp_db):
  repo = LogRepository()
  repo.create(DailyLogCreate(date=date(2026, 1, 1), journal_entry="Finished work", evening_completed=True, takeaway="Protect focus"))
  updated = repo.upsert_fields(date(2026, 1, 1), DailyLogUpdate(gratitude="A clear plan", morning_completed=True))
  assert updated.journal_entry == "Finished work"
  assert updated.takeaway == "Protect focus"
  assert updated.evening_completed is True


def test_score_and_weekly_writes_are_idempotent(temp_db):
  scores = ScoreRepository()
  scores.create(ScoreCreate(date=date(2026, 1, 1), scope="daily", overall_growth_score=10))
  scores.create(ScoreCreate(date=date(2026, 1, 1), scope="daily", overall_growth_score=20))
  assert scores.get_by_date(date(2026, 1, 1)).overall_growth_score == 20
  assert len(scores.get_recent(10)) == 1
  reviews = WeeklyReviewRepository()
  reviews.upsert(WeeklyReviewCreate(week_start=date(2026, 1, 5), week_end=date(2026, 1, 11), ai_output="one"))
  reviews.upsert(WeeklyReviewCreate(week_start=date(2026, 1, 5), week_end=date(2026, 1, 11), ai_output="two"))
  assert reviews.get_by_week_start(date(2026, 1, 5)).ai_output == "two"


def test_milestone_task_link_is_validated(temp_db):
  goal = GoalRepository().create(GoalCreate(title="Ship a release", category="career", horizon="quarterly"))
  milestone = MilestoneRepository().create(MilestoneCreate(goal_id=goal.id, title="Ship beta"))
  fields = serialize_journal_fields("", "", [{"id": "a", "text": "Test beta", "goal_id": goal.id, "milestone_id": milestone.id}])
  assert '"goal_id": ' in fields["planned_tasks"]


def test_memory_duplicate_and_lifecycle(temp_db):
  service = MemoryService()
  first = service.store("Protect the first hour", "lesson", source_type="test", source_id=1)
  second = service.store("  protect the first hour ", "lesson", source_type="test", source_id=1)
  assert first.id == second.id
  archived = service.update(first.id, status="archived")
  assert archived.status == "archived"
  assert service.count() == 0


def test_consent_defaults_to_disabled(temp_db):
  service = SettingsService()
  assert service.remote_ai_allowed() is False
  service.set_remote_ai_allowed(True)
  assert service.remote_ai_allowed() is True


def test_export_contains_new_tables(temp_db):
  payload = DataPortabilityService().export_payload()
  assert payload["format"] == "goalos-export"
  assert "milestones" in payload["tables"]
