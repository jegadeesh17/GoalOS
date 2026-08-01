"""Weekly Sync Service: Process weekly batch journal CSVs and generate weekly goal alignment reports."""

import csv
import io
from datetime import date, datetime, timedelta
from typing import Any

from database.connection import get_db
from database.repositories._helpers import row_to_dict


class WeeklySyncService:

  def parse_csv(self, file_content: str | bytes) -> list[dict[str, Any]]:
    """Parse CSV content of journal entries flexible across common headers."""
    if isinstance(file_content, bytes):
      file_content = file_content.decode("utf-8", errors="replace")

    reader = csv.DictReader(io.StringIO(file_content))
    entries = []
    for row in reader:
      # Normalize keys to lowercase stripped
      clean_row = {k.strip().lower(): v.strip() for k, v in row.items() if k}
      entry = {
        "date": clean_row.get("date") or clean_row.get("day") or "",
        "gratitude": clean_row.get("gratitude") or clean_row.get("morning_gratitude") or "",
        "tasks": clean_row.get("tasks") or clean_row.get("plans") or clean_row.get("to_do") or "",
        "wins": clean_row.get("wins") or clean_row.get("one_win") or clean_row.get("accomplishments") or "",
        "review": clean_row.get("review") or clean_row.get("journal_entry") or clean_row.get("reflections") or "",
        "takeaway": clean_row.get("takeaway") or clean_row.get("one_lesson") or clean_row.get("lesson") or "",
      }
      if entry["date"] or entry["review"] or entry["tasks"]:
        entries.append(entry)
    return entries

  def generate_weekly_report(self, entries: list[dict[str, Any]], active_goals: list[Any]) -> dict[str, Any]:
    """Generate a structured weekly synthesis and goal alignment report."""
    total_days = len(entries)
    all_wins = [e["wins"] for e in entries if e.get("wins")]
    all_takeaways = [e["takeaway"] for e in entries if e.get("takeaway")]
    all_reviews = [e["review"] for e in entries if e.get("review")]

    # Calculate basic goal alignment score based on journal presence and activity
    base_score = min(1.0, total_days / 7.0) if total_days > 0 else 0.0
    alignment_score = round(base_score * 100, 1)

    # Categorize goals by horizon
    short_term = [g for g in active_goals if getattr(g, "horizon", "").lower() in ("short", "weekly", "1-month")]
    one_year = [g for g in active_goals if getattr(g, "horizon", "").lower() in ("1-year", "1_year", "medium")]
    five_year = [g for g in active_goals if getattr(g, "horizon", "").lower() in ("5-year", "5_year", "long")]

    summary_parts = []
    summary_parts.append(f"Recorded {total_days} journal entries for the week.")
    if all_wins:
      summary_parts.append(f"Key Wins: {'; '.join(all_wins[:3])}")
    if all_takeaways:
      summary_parts.append(f"Key Takeaways: {'; '.join(all_takeaways[:3])}")

    next_week_focus = []
    if short_term:
      next_week_focus.append(f"Short-term focus: Execute tasks toward '{short_term[0].title}'")
    if one_year:
      next_week_focus.append(f"1-Year Goal Alignment: Maintain steady progress on '{one_year[0].title}'")
    if not next_week_focus:
      next_week_focus.append("Maintain consistent weekly journaling and protect deep work blocks.")

    return {
      "total_days_logged": total_days,
      "summary": "\n".join(summary_parts),
      "wins": "\n".join(f"• {w}" for w in all_wins) if all_wins else "No specific wins highlighted.",
      "lessons": "\n".join(f"• {t}" for t in all_takeaways) if all_takeaways else "No specific lessons highlighted.",
      "goal_alignment_score": alignment_score,
      "next_week_focus": "\n".join(f"1. {f}" for f in next_week_focus),
      "active_goals_count": len(active_goals),
    }

  def save_sync_log(
    self,
    week_start: date,
    week_end: date,
    source_type: str,
    raw_content: str,
    summary: str,
    wins: str,
    lessons: str,
    alignment_score: float,
    next_week_focus: str,
  ) -> int:
    with get_db() as conn:
      cur = conn.execute(
        """INSERT INTO weekly_sync_logs 
           (week_start, week_end, source_type, raw_content, summary, wins, lessons, goal_alignment_score, next_week_focus)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
          week_start.isoformat(),
          week_end.isoformat(),
          source_type,
          raw_content,
          summary,
          wins,
          lessons,
          alignment_score,
          next_week_focus,
        ),
      )
      log_id = cur.lastrowid
    return log_id

  def get_recent_sync_logs(self, limit: int = 10) -> list[dict[str, Any]]:
    with get_db() as conn:
      rows = conn.execute(
        "SELECT * FROM weekly_sync_logs ORDER BY week_start DESC LIMIT ?",
        (limit,),
      ).fetchall()
    return [row_to_dict(r) for r in rows]
