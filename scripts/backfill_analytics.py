"""Backfill analytics metrics (deep work, sleep, mood) and daily growth scores."""

from __future__ import annotations

import json
import re
import sqlite3
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
  sys.path.insert(0, str(ROOT))

from database.migrations import run_migrations
from database.repositories.goal_repository import GoalRepository
from database.repositories.log_repository import LogRepository
from database.repositories.score_repository import ScoreRepository
from models.daily_log import DailyLogUpdate
from services.analytics_service import calculate_daily_scores


def extract_deep_work_hours(plan_text: str, review_text: str, tasks_completed_text: str, completion_rate: float | None) -> float:
  """Heuristically extract focused deep work hours from journal time-blocks and notes."""
  combined = f"{plan_text or ''} {review_text or ''} {tasks_completed_text or ''}".lower()

  # Check explicit hour statements like "4 hours works", "3 hour work", "2.5 hours", "4h"
  match = re.search(r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|hour)\s*(?:works?|deep work|focus|coding)?", combined)
  if match:
    val = float(match.group(1))
    if 0.5 <= val <= 12.0:
      return round(val, 1)

  # Check time-block ranges for study/coding (e.g. 940-12, 10-12, 12-2, 7-9)
  work_block_hours = 0.0
  block_matches = re.findall(
    r"(\d{1,4})\s*-\s*(\d{1,4})\s+([a-zA-Z\s]+)", combined
  )
  for start_str, end_str, label in block_matches:
    label_lower = label.lower()
    if any(kw in label_lower for kw in ["code", "kata", "leetcode", "study", "prep", "nlp", "project", "work", "deploy", "resume", "learn", "quandao"]):
      try:
        s = int(start_str) if len(start_str) <= 2 else int(start_str[:2]) + int(start_str[2:]) / 60
        e = int(end_str) if len(end_str) <= 2 else int(end_str[:2]) + int(end_str[2:]) / 60
        if e < s:
          e += 12  # handle pm wrap
        dur = e - s
        if 0.25 <= dur <= 8.0:
          work_block_hours += dur
      except Exception:
        pass

  if work_block_hours > 0:
    return round(min(work_block_hours, 10.0), 1)

  # Fallback based on task completion rate
  if completion_rate is not None:
    if completion_rate >= 80.0:
      return 5.0
    if completion_rate >= 50.0:
      return 3.5
    if completion_rate >= 25.0:
      return 2.0
    return 1.0

  return 2.5


def extract_sleep_hours(review_text: str, takeaway_text: str) -> float:
  """Heuristically estimate sleep hours from reflections."""
  combined = f"{review_text or ''} {takeaway_text or ''}".lower()
  if any(kw in combined for kw in ["tired", "fatigue", "sleepy", "exhausted", "sleep deficit", "no energy", "low energy"]):
    return 5.5
  if any(kw in combined for kw in ["peaceful", "refreshed", "good sleep", "slept well"]):
    return 8.0
  return 7.2


def extract_mood(review_text: str, takeaway_text: str, completion_rate: float | None) -> int:
  """Heuristically estimate morning/vitality mood rating (1-5)."""
  combined = f"{review_text or ''} {takeaway_text or ''}".lower()
  if any(kw in combined for kw in ["porn", "wasted", "drifted", "doom scrolling", "never proceed", "slacking"]):
    return 2
  if completion_rate is not None and completion_rate >= 75.0:
    return 4
  if any(kw in combined for kw in ["grateful", "refresh", "stronger", "good day", "consistent", "accomplished"]):
    return 4
  return 3


def run_backfill(db_path: str = "goalos.db") -> dict[str, int]:
  run_migrations()
  log_repo = LogRepository()
  goal_repo = GoalRepository()
  score_repo = ScoreRepository()

  all_logs = log_repo.get_all()
  if not all_logs:
    print("No daily logs found to backfill.")
    return {"logs_updated": 0, "scores_generated": 0}

  # Sort chronologically ascending for cumulative score calculation
  all_logs_sorted = sorted(all_logs, key=lambda l: l.date)
  logs_updated = 0

  print(f"Enhancing {len(all_logs_sorted)} daily logs with metrics...")
  for log in all_logs_sorted:
    updates: dict[str, any] = {}
    if log.deep_work_hours is None or log.deep_work_hours == 0:
      updates["deep_work_hours"] = extract_deep_work_hours(
        log.time_blocks or "",
        log.journal_entry or "",
        log.tasks_completed or "",
        log.task_completion_rate,
      )
    if log.sleep_hours is None or log.sleep_hours == 0:
      updates["sleep_hours"] = extract_sleep_hours(log.journal_entry or "", log.takeaway or "")
    if log.mood_morning is None:
      updates["mood_morning"] = extract_mood(log.journal_entry or "", log.takeaway or "", log.task_completion_rate)
    if log.energy_level is None:
      updates["energy_level"] = 3 if updates.get("mood_morning", 3) >= 3 else 2
    if log.sleep_quality is None:
      updates["sleep_quality"] = 4 if updates.get("sleep_hours", 7.0) >= 7.0 else 3
    if log.expected_focus is None:
      updates["expected_focus"] = 4 if updates.get("deep_work_hours", 2.0) >= 3.0 else 3

    if updates:
      log_repo.update(log.id, DailyLogUpdate(**updates))
      logs_updated += 1

  # Now recalculate scores chronologically
  refreshed_logs = sorted(log_repo.get_all(), key=lambda l: l.date)
  goals = goal_repo.get_active()
  scores_generated = 0

  print(f"Calculating and persisting daily growth scores...")
  for idx, log in enumerate(refreshed_logs):
    start_date = log.date - timedelta(days=30)
    logs_30d = [l for l in refreshed_logs if start_date <= l.date <= log.date]
    
    # Get 7-day prior scores
    recent_scores = score_repo.get_recent(last_n=7)
    scores_7d = [s.overall_growth_score or 50.0 for s in recent_scores] if recent_scores else [50.0]
    
    calculate_daily_scores(log, goals, logs_30d, scores_7d)
    scores_generated += 1

  print(f"Backfill complete! Updated {logs_updated} logs and generated {scores_generated} daily scores.")
  return {"logs_updated": logs_updated, "scores_generated": scores_generated}


if __name__ == "__main__":
  run_backfill()
