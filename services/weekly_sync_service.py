import csv
import io
import os
from datetime import date, timedelta
from typing import Any

from database.connection import get_db
from database.repositories._helpers import row_to_dict
from database.repositories.goal_repository import GoalRepository
from database.repositories.log_repository import LogRepository
from models.daily_log import DailyLogUpdate
from services.local_ocr_service import extract_text_from_image, parse_ocr_text_to_standard_fields


class WeeklySyncService:

  def parse_csv(self, file_content: str | bytes) -> list[dict[str, Any]]:
    """Parse CSV content of journal entries flexible across common headers."""
    if isinstance(file_content, bytes):
      file_content = file_content.decode("utf-8", errors="replace")

    reader = csv.DictReader(io.StringIO(file_content))
    entries = []
    for row in reader:
      clean_row = {k.strip().lower(): v.strip() for k, v in row.items() if k}
      entry = {
        "date": clean_row.get("date") or clean_row.get("day") or "",
        "gratitude": clean_row.get("gratitude") or clean_row.get("morning_gratitude") or "",
        "tasks": clean_row.get("tasks") or clean_row.get("plans") or clean_row.get("to_do") or "",
        "plan": clean_row.get("plan") or clean_row.get("time_blocks") or clean_row.get("schedule") or "",
        "wins": clean_row.get("wins") or clean_row.get("one_win") or clean_row.get("accomplishments") or "",
        "review": clean_row.get("review") or clean_row.get("journal_entry") or clean_row.get("reflections") or "",
        "takeaway": clean_row.get("takeaway") or clean_row.get("one_lesson") or clean_row.get("lesson") or "",
      }
      if entry["date"] or entry["review"] or entry["tasks"]:
        entries.append(entry)
    return entries

  def scan_journal_folder(
    self,
    folder_path: str,
    start_date: date = date(2026, 7, 1),
    persist_to_db: bool = True,
  ) -> list[dict[str, Any]]:
    """Scan folder of handwritten journal page images, extract structured text using local OCR, and persist to DB as text."""
    if not os.path.exists(folder_path):
      return []

    valid_exts = (".jpg", ".jpeg", ".png")
    files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith(valid_exts)])
    entries = []
    log_repo = LogRepository()

    for index, filename in enumerate(files):
      file_path = os.path.join(folder_path, filename)
      entry_date = start_date + timedelta(days=index)
      day_label = f"Day {index + 1} ({entry_date.strftime('%B %d, %Y')})"

      # Attempt local OCR read without any external API calls
      raw_ocr_text = ""
      try:
        with open(file_path, "rb") as f:
          ocr_res = extract_text_from_image(f.read())
          if ocr_res.get("success"):
            raw_ocr_text = ocr_res.get("text", "")
      except Exception:
        pass

      # Format extracted raw text into the July standard 5-part structure
      structured = parse_ocr_text_to_standard_fields(raw_ocr_text, day_label=day_label)

      entry_data = {
        "day_number": index + 1,
        "filename": filename,
        "date": entry_date.isoformat(),
        "gratitude": structured["gratitude"],
        "tasks": structured["tasks"],
        "plan": structured["plan"],
        "review": structured["review"],
        "takeaway": structured["takeaway"],
        "raw_ocr": raw_ocr_text,
      }

      # Persist structured textual content directly into SQLite daily_logs table (No images saved in DB)
      if persist_to_db:
        try:
          changes = DailyLogUpdate(
            gratitude=structured["gratitude"],
            planned_tasks=structured["tasks"],
            time_blocks=structured["plan"],
            journal_entry=structured["review"],
            takeaway=structured["takeaway"],
            evening_completed=True,
            imported=True,
            import_source=f"batch_ocr:{filename}",
          )
          log_repo.upsert_fields(entry_date, changes)
        except Exception:
          pass

      entries.append(entry_data)
    return entries

  def group_entries_into_weeks(self, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group entries into 7-day calendar weeks."""
    if not entries:
      return []

    sorted_entries = sorted(entries, key=lambda x: x.get("date", ""))
    chunks = []
    chunk_size = 7

    for i in range(0, len(sorted_entries), chunk_size):
      week_entries = sorted_entries[i : i + chunk_size]
      first_date = date.fromisoformat(week_entries[0]["date"]) if week_entries[0].get("date") else date.today()
      last_date = date.fromisoformat(week_entries[-1]["date"]) if week_entries[-1].get("date") else first_date

      chunks.append(
        {
          "week_index": (i // chunk_size) + 1,
          "week_start": first_date.isoformat(),
          "week_end": last_date.isoformat(),
          "entries": week_entries,
          "days_count": len(week_entries),
        }
      )
    return chunks

  def generate_weekly_report(
    self,
    entries: list[dict[str, Any]],
    active_goals: list[Any] = None,
    week_index: int = 1,
    total_weeks_in_month: int = 4,
  ) -> dict[str, Any]:
    """Generate a structured weekly synthesis, 1-Month goal pacing report, and urgent takeaways."""
    if active_goals is None:
      active_goals = GoalRepository().get_active()

    total_days = len(entries)
    all_reviews = [e.get("review", "") for e in entries if e.get("review")]
    all_takeaways = [e.get("takeaway", "") for e in entries if e.get("takeaway")]

    base_score = min(1.0, total_days / 7.0) if total_days > 0 else 0.0
    alignment_score = round(base_score * 100, 1)

    # Categorize goals by horizon
    categorized_goals = GoalRepository().get_by_horizons()
    short_term_goals = categorized_goals.get("1-month", [])
    one_year_goals = categorized_goals.get("1-year", [])
    five_year_goals = categorized_goals.get("5-year", [])

    weeks_remaining = max(0, total_weeks_in_month - week_index)

    # Urgent coaching takeaway calculation
    urgent_takeaway = ""
    if total_days < 5:
      urgent_takeaway = f"You logged only {total_days}/7 days this week. You have {weeks_remaining} weeks remaining in the month. Focus on completing deep work first thing in the morning."
    elif short_term_goals:
      primary_goal = short_term_goals[0].title
      urgent_takeaway = f"Week {week_index} of {total_weeks_in_month} complete ({weeks_remaining} weeks remaining). Lock in morning deep work blocks to achieve: '{primary_goal}'."
    else:
      urgent_takeaway = f"Week {week_index} complete. Define your 1-Month short-term goals to maximize your weekly ROI."

    # Task to Goal mapping narrative
    mapped_tasks = []
    for goal in short_term_goals[:2]:
      mapped_tasks.append(f"Short-Term Goal (1-Month): '{goal.title}' ➔ Daily planned tasks aligned.")
    for goal in one_year_goals[:2]:
      mapped_tasks.append(f"Mid-Term Goal (1-Year): '{goal.title}' ➔ Weekly momentum required.")

    return {
      "week_index": week_index,
      "weeks_remaining_in_month": weeks_remaining,
      "total_days_logged": total_days,
      "goal_alignment_score": alignment_score,
      "urgent_coaching_takeaway": urgent_takeaway,
      "task_goal_mapping": "\n".join(f"• {m}" for m in mapped_tasks) if mapped_tasks else "No active 1-Month or 1-Year goals mapped.",
      "summary": f"Logged {total_days}/7 days in Week {week_index}. " + (f"Key takeaway: {all_takeaways[0]}" if all_takeaways else ""),
      "wins": "\n".join(f"• {r[:80]}..." for r in all_reviews[:3]) if all_reviews else "Journal reflections recorded.",
      "takeaways": "\n".join(f"• {t}" for t in all_takeaways[:3]) if all_takeaways else "Maintain consistency.",
      "short_term_goals": [g.title for g in short_term_goals],
      "one_year_goals": [g.title for g in one_year_goals],
      "five_year_goals": [g.title for g in five_year_goals],
    }

  def generate_monthly_report(
    self,
    weekly_reports: list[dict[str, Any]],
    month_name: str = "July 2026",
  ) -> dict[str, Any]:
    """Aggregate weekly reports and evaluate Cascading Goal Impact (Monthly -> Yearly -> 5-Year)."""
    total_days = sum(r.get("total_days_logged", 0) for r in weekly_reports)
    avg_score = round(sum(r.get("goal_alignment_score", 0.0) for r in weekly_reports) / max(1, len(weekly_reports)), 1)

    categorized_goals = GoalRepository().get_by_horizons()
    one_year_goals = categorized_goals.get("1-year", [])
    five_year_goals = categorized_goals.get("5-year", [])

    # Calculate cascading impact
    cascading_impact = []
    if avg_score >= 80.0:
      cascading_impact.append(f"High monthly consistency ({avg_score}%) accelerates your 1-Year goal milestones.")
      if five_year_goals:
        cascading_impact.append(f"On track to achieve 5-Year Vision: '{five_year_goals[0].title}'.")
    else:
      cascading_impact.append(f"Monthly execution score ({avg_score}%) was sub-optimal. Next month requires doubling deep work focus.")
      if one_year_goals:
        cascading_impact.append(f"Warning: Progress toward 1-Year Goal '{one_year_goals[0].title}' is at risk of falling behind schedule.")

    return {
      "month": month_name,
      "total_weeks": len(weekly_reports),
      "total_days_logged": total_days,
      "average_goal_alignment": avg_score,
      "cascading_goal_impact": "\n".join(f"• {ci}" for ci in cascading_impact),
      "monthly_takeaway": f"Completed {total_days} total logged days in {month_name} with an average alignment score of {avg_score}%.",
      "weekly_summaries": [r.get("summary") for r in weekly_reports if r.get("summary")],
    }

  # Backward compatibility alias
  generate_monthly_summary = generate_monthly_report

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
          week_start.isoformat() if isinstance(week_start, date) else str(week_start),
          week_end.isoformat() if isinstance(week_end, date) else str(week_end),
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
