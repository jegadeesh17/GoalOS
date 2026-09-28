"""Build the public demo database from the FICTIONAL journal in data/demo_seed.csv.

Produces data/demo_goalos.db and data/demo_chroma_db/, which the Dockerfile ships
to Cloud Run. Everything is built from fictional persona data (see
scripts/generate_demo_journal.py) through the same code paths real data takes:
  - daily logs:  scripts/import_journal_csv.run_import
  - memories:    JournalImportService._extract_memories
  - scores:      scripts/backfill_analytics.run_backfill

Never point this at a real journal or copy goalos.db into the demo outputs;
this repository and the demo are public.

Usage: python scripts/build_demo_db.py
"""

import csv
import gc
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED_CSV = ROOT / "data" / "demo_seed.csv"
OUT_DB = ROOT / "data" / "demo_goalos.db"
OUT_CHROMA = ROOT / "data" / "demo_chroma_db"

PERSONA = {"name": "Alex Chen", "birth_date": "1998-11-03", "target_age": 80}

# (title, category, horizon, deadline, priority, progress, success_criteria)
GOALS = [
  ("Ship v1 of the recipe-search API", "career", "1-month", date(2026, 9, 30), 5, 0.6,
   "Public endpoint deployed with tests and a README"),
  ("Run 3 times a week", "health", "1-month", date(2026, 9, 30), 4, 0.5,
   "12 logged runs this month"),
  ("Land an ML engineer role", "career", "1-year", date(2027, 6, 30), 5, 0.2,
   "Signed offer for an ML engineering position"),
  ("Run a half marathon", "health", "1-year", date(2027, 3, 31), 4, 0.25,
   "Finish 21.1 km under 2 hours"),
  ("Read 12 technical books", "personal", "1-year", date(2026, 12, 31), 3, 0.4,
   "Notes written for each book"),
  ("Lead an applied ML team", "career", "5-year", date(2031, 6, 30), 4, 0.05,
   "Managing a team shipping ML features to production"),
  ("Save a house down payment", "finance", "5-year", date(2030, 12, 31), 4, 0.15,
   "Down payment saved without touching the emergency fund"),
  ("Run an independent product studio", "career", "10-year", date(2036, 12, 31), 3, 0.0,
   "Two profitable products paying a full salary"),
  ("Reach financial independence", "finance", "10-year", date(2036, 12, 31), 3, 0.05,
   "Investments cover yearly expenses"),
]


def build(workdir: Path) -> dict[str, int]:
  db_path = workdir / "demo_goalos.db"
  chroma_path = workdir / "demo_chroma_db"
  # Settings are read at import time, so point them at the scratch outputs first.
  # ENVIRONMENT=demo matches Cloud Run, so memories are embedded the same way the demo queries them.
  os.environ.update(DB_PATH=str(db_path), CHROMA_PATH=str(chroma_path), ENVIRONMENT="demo")
  if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

  from database.connection import get_db
  from database.migrations import run_migrations
  from database.repositories.goal_repository import GoalRepository
  from database.repositories.log_repository import LogRepository
  from models.goal import GoalCreate
  from scripts.backfill_analytics import run_backfill
  from scripts.import_journal_csv import run_import
  from services.journal_import_service import JournalImportService

  run_migrations()
  with get_db() as conn:
    conn.execute("INSERT OR IGNORE INTO user (id, name) VALUES (1, ?)", (PERSONA["name"],))
    conn.execute(
      "UPDATE user SET name = ?, birth_date = ?, target_age = ? WHERE id = 1",
      (PERSONA["name"], PERSONA["birth_date"], PERSONA["target_age"]),
    )
    conn.execute(
      "INSERT OR REPLACE INTO settings (key, value) VALUES ('remote_ai_consent', 'true')"
    )

  goal_repo = GoalRepository()
  for title, category, horizon, deadline, priority, progress, criteria in GOALS:
    goal_repo.create(GoalCreate(
      title=title, category=category, horizon=horizon, deadline=deadline,
      priority=priority, progress=progress, success_criteria=criteria,
    ))

  logs = run_import(csv_path=str(SEED_CSV), db_path=str(db_path))

  svc = JournalImportService()
  log_repo = LogRepository()
  memories = 0
  with open(SEED_CSV, encoding="utf-8") as f:
    for row in csv.DictReader(f):
      entry = svc.parse_entry(row)
      stored = log_repo.get_by_date(entry.date)
      memories += svc._extract_memories(entry, stored.id)

  scores = run_backfill(str(db_path))["scores_generated"]
  return {"logs": logs, "goals": len(GOALS), "memories": memories, "scores": scores}


def main() -> None:
  staging = Path(tempfile.mkdtemp(prefix="goalos-demo-"))
  counts = build(staging)

  # Release Chroma's cached client so its files can be copied and removed on Windows.
  from services.memory_service import clear_collection_cache
  clear_collection_cache()
  gc.collect()

  if OUT_DB.exists():
    OUT_DB.unlink()
  src = sqlite3.connect(str(staging / "demo_goalos.db"))
  dst = sqlite3.connect(str(OUT_DB))
  src.backup(dst)  # backup API folds any WAL content into the copy
  dst.close()
  src.close()

  if OUT_CHROMA.exists():
    shutil.rmtree(OUT_CHROMA)
  shutil.copytree(staging / "demo_chroma_db", OUT_CHROMA)
  shutil.rmtree(staging, ignore_errors=True)
  print(f"Built {OUT_DB.relative_to(ROOT)} and {OUT_CHROMA.relative_to(ROOT)}: {counts}")


if __name__ == "__main__":
  main()
