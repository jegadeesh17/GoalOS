"""Repository layer tests."""

from datetime import date

from database.repositories.coach_repository import CoachRepository
from database.repositories.goal_repository import GoalRepository
from database.repositories.log_repository import LogRepository
from database.repositories.memory_repository import MemoryRepository
from database.repositories.score_repository import ScoreRepository
from models.coach_response import CoachResponseCreate
from models.daily_log import DailyLogCreate, DailyLogUpdate
from models.goal import GoalUpdate
from models.memory import MemoryCreate
from models.score import ScoreCreate


class TestGoalRepository:
  def test_create_and_get(self, temp_db, sample_goal):
    repo = GoalRepository()
    created = repo.create(sample_goal)
    assert created.id is not None
    assert created.title == "Learn Python"
    fetched = repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.category == "learning"

  def test_get_active(self, temp_db, sample_goal):
    repo = GoalRepository()
    repo.create(sample_goal)
    active = repo.get_active()
    assert len(active) == 1

  def test_update(self, temp_db, sample_goal):
    repo = GoalRepository()
    created = repo.create(sample_goal)
    updated = repo.update(created.id, GoalUpdate(progress=0.5))
    assert updated.progress == 0.5

  def test_delete(self, temp_db, sample_goal):
    repo = GoalRepository()
    created = repo.create(sample_goal)
    assert repo.delete(created.id) is True
    assert repo.get_by_id(created.id) is None


class TestLogRepository:
  def test_create_and_get_by_date(self, temp_db, sample_log):
    repo = LogRepository()
    created = repo.create(sample_log)
    assert created.id is not None
    fetched = repo.get_by_date(date(2026, 6, 23))
    assert fetched is not None
    assert fetched.top_priority == "Solve Codekata problems"

  def test_get_recent(self, temp_db):
    repo = LogRepository()
    repo.create(DailyLogCreate(date=date(2026, 6, 20), morning_completed=True))
    repo.create(DailyLogCreate(date=date(2026, 6, 21), morning_completed=True))
    recent = repo.get_recent(5)
    assert len(recent) == 2

  def test_upsert(self, temp_db, sample_log):
    repo = LogRepository()
    repo.upsert_by_date(sample_log)
    updated_log = DailyLogCreate(
      date=date(2026, 6, 23),
      top_priority="Updated priority",
    )
    result = repo.upsert_by_date(updated_log)
    assert result.top_priority == "Updated priority"

  def test_update(self, temp_db, sample_log):
    repo = LogRepository()
    created = repo.create(sample_log)
    updated = repo.update(created.id, DailyLogUpdate(one_win="Finished 10 problems"))
    assert updated.one_win == "Finished 10 problems"


class TestScoreRepository:
  def test_create_and_get_by_date(self, temp_db):
    repo = ScoreRepository()
    score = ScoreCreate(
      date=date(2026, 6, 23),
      scope="daily",
      overall_growth_score=75.0,
      consistency_score=80.0,
    )
    created = repo.create(score)
    assert created.id is not None
    fetched = repo.get_by_date(date(2026, 6, 23))
    assert fetched is not None
    assert fetched.overall_growth_score == 75.0

  def test_get_recent(self, temp_db):
    repo = ScoreRepository()
    for d in range(20, 23):
      repo.create(ScoreCreate(date=date(2026, 6, d), scope="daily", overall_growth_score=float(d)))
    recent = repo.get_recent(2)
    assert len(recent) == 2


class TestMemoryRepository:
  def test_create_and_get(self, temp_db):
    repo = MemoryRepository()
    memory = MemoryCreate(text="Focus on what matters", type="lesson", importance=0.8)
    created = repo.create(memory)
    fetched = repo.get_by_id(created.id)
    assert fetched.text == "Focus on what matters"

  def test_get_by_type(self, temp_db):
    repo = MemoryRepository()
    repo.create(MemoryCreate(text="I will run tomorrow", type="commitment", importance=0.7))
    repo.create(MemoryCreate(text="Great workout", type="achievement", importance=0.6))
    commitments = repo.get_by_type("commitment")
    assert len(commitments) == 1

  def test_increment_access(self, temp_db):
    repo = MemoryRepository()
    created = repo.create(MemoryCreate(text="Test", type="lesson"))
    repo.increment_access(created.id)
    fetched = repo.get_by_id(created.id)
    assert fetched.access_count == 1


class TestCoachRepository:
  def test_create_and_get_recent(self, temp_db):
    repo = CoachRepository()
    response = CoachResponseCreate(
      session_type="morning",
      ai_response='{"focus_statement": "Code"}',
      date=date(2026, 6, 23),
    )
    repo.create(response)
    recent = repo.get_recent(1)
    assert len(recent) == 1
    assert recent[0].session_type == "morning"

  def test_get_by_session_type(self, temp_db):
    repo = CoachRepository()
    repo.create(CoachResponseCreate(
      session_type="evening",
      ai_response="{}",
      date=date(2026, 6, 23),
    ))
    results = repo.get_by_session_type("evening")
    assert len(results) == 1
