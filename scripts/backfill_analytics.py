"""Recalculate daily growth scores from real DailyLog fields only.

Previously this also fabricated deep_work_hours/sleep_hours/mood_morning/
energy_level/sleep_quality/expected_focus via keyword-matching heuristics
whenever those fields were missing. That guesswork has been removed: this
script now only recomputes scores.overall_growth_score (and its components)
from whatever real fields a log actually has. A log missing sleep/mood/
deep-work data simply gets a lower/partial health or productivity score
instead of a fabricated one — never invent values for missing fields here.
"""

from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
  sys.path.insert(0, str(ROOT))

from database.migrations import run_migrations
from database.repositories.goal_repository import GoalRepository
from database.repositories.log_repository import LogRepository
from database.repositories.score_repository import ScoreRepository
from services.analytics_service import calculate_daily_scores


def run_backfill(db_path: str = "goalos.db") -> dict[str, int]:
  run_migrations()
  log_repo = LogRepository()
  goal_repo = GoalRepository()
  score_repo = ScoreRepository()

  all_logs = log_repo.get_all()
  if not all_logs:
    print("No daily logs found to backfill.")
    return {"scores_generated": 0}

  # Recalculate scores chronologically, using only whatever real fields each log has.
  logs_sorted = sorted(all_logs, key=lambda l: l.date)
  goals = goal_repo.get_active()
  scores_generated = 0

  print(f"Calculating and persisting daily growth scores for {len(logs_sorted)} logs...")
  for log in logs_sorted:
    start_date = log.date - timedelta(days=30)
    logs_30d = [l for l in logs_sorted if start_date <= l.date <= log.date]

    # Get 7-day prior scores
    recent_scores = score_repo.get_recent(last_n=7)
    scores_7d = [s.overall_growth_score or 50.0 for s in recent_scores] if recent_scores else [50.0]

    calculate_daily_scores(log, goals, logs_30d, scores_7d)
    scores_generated += 1

  print(f"Backfill complete! Generated {scores_generated} daily scores from real data only.")
  return {"scores_generated": scores_generated}


if __name__ == "__main__":
  run_backfill()
