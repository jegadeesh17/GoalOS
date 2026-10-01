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
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
  sys.path.insert(0, str(ROOT))

from database.migrations import run_migrations
from database.repositories.log_repository import LogRepository
from services.analytics_service import recompute_all_scores
from services.monthly_analytics_service import MonthlyAnalyticsService


def run_backfill(db_path: str = "goalos.db") -> dict[str, int]:
  run_migrations()
  if not LogRepository().get_all():
    print("No daily logs found to backfill.")
    return {"scores_generated": 0}

  # Chronological, using only whatever real fields each log has; alignment reads the saved task links.
  print("Calculating and persisting daily growth scores...")
  scores_generated = recompute_all_scores()

  # Monthly snapshots average these scores, so rebuild them (facts and levers) afterwards.
  months = MonthlyAnalyticsService().recompute_all()
  print(f"Backfill complete! Generated {scores_generated} daily scores and {len(months)} monthly snapshots from real data only.")
  return {"scores_generated": scores_generated}


if __name__ == "__main__":
  run_backfill()
