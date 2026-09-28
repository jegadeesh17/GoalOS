"""Demo data must only ever load in the demo environment, never into a local real DB."""

import sqlite3
import tempfile
from pathlib import Path

from config import settings as settings_module


def _log_count(db_path: str) -> int:
  conn = sqlite3.connect(db_path)
  try:
    return conn.execute("SELECT count(*) FROM daily_logs").fetchone()[0]
  finally:
    conn.close()


def test_seeder_does_nothing_outside_demo(temp_db, monkeypatch):
  from services.demo_seeder import seed_demo_environment

  missing_chroma = Path(tempfile.mkdtemp()) / "chroma"
  monkeypatch.setattr(settings_module.settings, "CHROMA_PATH", str(missing_chroma))
  monkeypatch.setattr(settings_module.settings, "ENVIRONMENT", "development")

  seed_demo_environment()

  assert _log_count(temp_db) == 0
  assert not missing_chroma.exists()


def test_seeder_loads_demo_data_in_demo(temp_db, monkeypatch):
  from services.demo_seeder import seed_demo_environment

  monkeypatch.setattr(settings_module.settings, "ENVIRONMENT", "demo")

  results = seed_demo_environment()

  assert results["logs_loaded"] > 0
  assert _log_count(temp_db) == results["logs_loaded"]


def test_csv_import_never_falls_back_to_demo_seed_outside_demo(temp_db, monkeypatch):
  from scripts.import_journal_csv import run_import

  monkeypatch.setattr(settings_module.settings, "ENVIRONMENT", "development")
  missing_csv = Path(tempfile.mkdtemp()) / "journal_data.csv"

  imported = run_import(csv_path=str(missing_csv), db_path=temp_db)

  assert imported == 0
  assert _log_count(temp_db) == 0
