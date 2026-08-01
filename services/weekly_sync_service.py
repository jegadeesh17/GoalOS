import calendar
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
        "file_path": file_path,
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

  def calculate_monthly_progress(
    self,
    entries: list[dict[str, Any]],
    month_start: date = None,
    month_name: str = "",
    active_goals: list[Any] = None,
  ) -> dict[str, Any]:
    """Calculate progress continuously based on logged entries in the month vs total days in month."""
    if not month_start:
      month_start = date.today().replace(day=1)
    if not month_name:
      month_name = month_start.strftime("%B %Y")

    days_in_month = calendar.monthrange(month_start.year, month_start.month)[1]

    # Filter entries that belong to target month/year
    month_entries = []
    for e in entries:
      edate = e.get("date")
      if isinstance(edate, str):
        try:
          edate = date.fromisoformat(edate[:10])
        except Exception:
          edate = None
      if isinstance(edate, date):
        if edate.year == month_start.year and edate.month == month_start.month:
          month_entries.append(e)
      else:
        month_entries.append(e)

    days_logged = len(month_entries)
    completion_rate = round((days_logged / days_in_month) * 100, 1) if days_in_month > 0 else 0.0

    target_entries = month_entries
    all_reviews = [e.get("review", "") or e.get("journal_entry", "") for e in target_entries if e.get("review") or e.get("journal_entry")]
    all_takeaways = [e.get("takeaway", "") or e.get("gratitude", "") for e in target_entries if e.get("takeaway") or e.get("gratitude")]
    all_tasks = [e.get("tasks", "") or e.get("planned_tasks", "") for e in target_entries if e.get("tasks") or e.get("planned_tasks")]

    categorized_goals = GoalRepository().get_goals_for_month(month_start)
    short_term_goals = categorized_goals.get("1-month", [])
    one_year_goals = categorized_goals.get("1-year", [])
    five_year_goals = categorized_goals.get("5-year", [])

    primary_1m_goal = short_term_goals[0].title if short_term_goals else "Establish core daily habits"

    # Pacing assessment
    if completion_rate >= 80.0:
      pacing_status = "On Track — High Execution"
      coaching_takeaway = f"Excellent consistency in {month_name} ({days_logged}/{days_in_month} days). Keep momentum focused on: '{primary_1m_goal}'."
    elif completion_rate >= 40.0:
      pacing_status = "Moderate Pacing — Step Up Morning Focus"
      coaching_takeaway = f"Logged {days_logged}/{days_in_month} days so far in {month_name}. Protect your morning deep work block to hit '{primary_1m_goal}'."
    else:
      pacing_status = "Behind Schedule — Reset Daily Discipline"
      coaching_takeaway = f"Only {days_logged}/{days_in_month} days logged in {month_name}. Lock in a daily 60-min focus block for '{primary_1m_goal}'."

    wins_str = "\n".join(f"• {r[:80]}..." for r in all_reviews[:4]) if all_reviews else "Journal reflections recorded."
    takeaways_str = "\n".join(f"• {t}" for t in all_takeaways[:4]) if all_takeaways else "Maintain consistency."

    return {
      "month_name": month_name,
      "days_logged": days_logged,
      "days_in_month": days_in_month,
      "monthly_completion_rate": completion_rate,
      "pacing_status": pacing_status,
      "coaching_takeaway": coaching_takeaway,
      "primary_monthly_goal": primary_1m_goal,
      "short_term_goals": [g.title for g in short_term_goals],
      "one_year_goals": [g.title for g in one_year_goals],
      "five_year_goals": [g.title for g in five_year_goals],
      "wins": wins_str,
      "takeaways": takeaways_str,
      "tasks_summary": "\n".join(f"• {t[:60]}" for t in all_tasks[:5]) if all_tasks else "Daily task logs captured.",
      "is_month_complete": days_logged >= days_in_month,
    }

  def generate_monthly_report(
    self,
    entries_or_reports: list[dict[str, Any]],
    month_name: str = "July 2026",
    active_goals: list[Any] = None,
    month_start: date = None,
  ) -> dict[str, Any]:
    """Aggregate month's data and evaluate Cascading Goal Impact (Monthly -> Yearly -> 5-Year)."""
    if not month_start:
      month_start = date.today().replace(day=1)

    categorized_goals = GoalRepository().get_goals_for_month(month_start)
    short_term_goals = categorized_goals.get("1-month", [])
    one_year_goals = categorized_goals.get("1-year", [])
    five_year_goals = categorized_goals.get("5-year", [])

    total_days = len(entries_or_reports)
    days_in_m = calendar.monthrange(month_start.year, month_start.month)[1]
    avg_score = round((total_days / float(days_in_m)) * 100, 1) if days_in_m > 0 else 0.0

    primary_1m = short_term_goals[0].title if short_term_goals else "Core Execution"
    y1_titles = [f"'{g.title}'" for g in one_year_goals] if one_year_goals else ["1-Year Milestones"]
    y5_titles = [f"'{g.title}'" for g in five_year_goals] if five_year_goals else ["5-Year Vision"]

    cascading_impact = []
    if avg_score >= 70.0:
      cascading_impact.append(f"High consistency in {month_name} ({total_days}/{days_in_m} days logged, {avg_score}%) directly advances your 1-Year Goals: {', '.join(y1_titles)}.")
      if five_year_goals:
        cascading_impact.append(f"Accelerates long-term trajectory toward your 5-Year Goals: {', '.join(y5_titles)}.")
    else:
      cascading_impact.append(f"Execution in {month_name} ({total_days}/{days_in_m} days logged, {avg_score}%) was sub-optimal. Next month requires doubling morning focus.")
      if one_year_goals:
        cascading_impact.append(f"Warning: 1-Year Goal milestones ({', '.join(y1_titles)}) risk falling behind schedule.")

    return {
      "month": month_name,
      "total_days_logged": total_days,
      "average_goal_alignment": avg_score,
      "cascading_goal_impact": "\n".join(f"• {ci}" for ci in cascading_impact),
      "monthly_takeaway": f"Completed {total_days} total logged days in {month_name} with an alignment score of {avg_score}%.",
    }

  def generate_yearly_report(
    self,
    monthly_reports: list[dict[str, Any]],
    year_name: str = "2026",
    active_goals: list[Any] = None,
  ) -> dict[str, Any]:
    """Aggregate monthly reports into an annual 1-Year Goal impact report."""
    total_months = len(monthly_reports)
    total_days = sum(m.get("total_days_logged", 0) for m in monthly_reports)
    avg_alignment = round(sum(m.get("average_goal_alignment", 0.0) for m in monthly_reports) / max(1, total_months), 1)

    categorized_goals = GoalRepository().get_by_horizons()
    one_year_goals = categorized_goals.get("1-year", [])
    five_year_goals = categorized_goals.get("5-year", [])

    annual_verdict = ""
    if avg_alignment >= 75.0:
      annual_verdict = f"Outstanding annual execution ({avg_alignment}% alignment over {total_months} months). 1-Year goals achieved!"
    else:
      annual_verdict = f"Pacing behind full 1-Year capacity ({avg_alignment}% alignment over {total_months} months). Recalibrate 1-Month milestones."

    return {
      "year": year_name,
      "total_months": total_months,
      "total_days_logged": total_days,
      "annual_alignment_score": avg_alignment,
      "annual_verdict": annual_verdict,
      "one_year_goals": [g.title for g in one_year_goals],
      "five_year_goals": [g.title for g in five_year_goals],
    }

  # Backward compatibility aliases
  def group_entries_into_weeks(self, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Legacy helper: group entries into chunks for backwards compatibility."""
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
    """Legacy wrapper for weekly report formatting."""
    progress = self.calculate_monthly_progress(entries, active_goals=active_goals)
    return {
      "week_index": week_index,
      "weeks_remaining_in_month": 4 - week_index,
      "total_days_logged": len(entries),
      "goal_alignment_score": progress["monthly_completion_rate"],
      "urgent_coaching_takeaway": progress["coaching_takeaway"],
      "next_week_focus": progress["coaching_takeaway"],
      "task_goal_mapping": f"1-Month Goal: '{progress['primary_monthly_goal']}'",
      "summary": f"Logged {len(entries)} days in month chunk.",
      "wins": progress["wins"],
      "takeaways": progress["takeaways"],
      "lessons": progress["takeaways"],
      "short_term_goals": progress["short_term_goals"],
      "one_year_goals": progress["one_year_goals"],
      "five_year_goals": progress["five_year_goals"],
    }

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
