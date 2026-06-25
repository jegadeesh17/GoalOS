"""Pytest configuration and fixtures."""

import os
import tempfile
from datetime import date

import pytest

os.environ.setdefault("OPENROUTER_API_KEY", "test-key")


@pytest.fixture
def temp_db(monkeypatch):
  """Create a temporary database for each test."""
  import services.memory_service as ms

  ms._COLLECTION = None

  with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
    db_path = f.name
  chroma_dir = tempfile.mkdtemp()
  monkeypatch.setenv("DB_PATH", db_path)
  monkeypatch.setenv("CHROMA_PATH", chroma_dir)
  from config import settings

  monkeypatch.setattr(settings.settings, "DB_PATH", db_path)
  monkeypatch.setattr(settings.settings, "CHROMA_PATH", chroma_dir)
  from database.migrations import run_migrations

  run_migrations()
  yield db_path
  ms._COLLECTION = None
  try:
    os.unlink(db_path)
  except OSError:
    pass
  import shutil
  try:
    shutil.rmtree(chroma_dir, ignore_errors=True)
  except OSError:
    pass


@pytest.fixture
def sample_goal():
  from models.goal import GoalCreate

  return GoalCreate(
    title="Learn Python",
    category="learning",
    horizon="quarterly",
    reason="Become a better developer",
  )


@pytest.fixture
def sample_log():
  from models.daily_log import DailyLogCreate

  return DailyLogCreate(
    date=date(2026, 6, 23),
    morning_completed=True,
    top_priority="Solve Codekata problems",
    evening_completed=True,
    journal_entry="Good day of coding",
  )
