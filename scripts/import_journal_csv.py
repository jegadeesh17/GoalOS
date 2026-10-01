"""Robust Journal CSV Import Script for GoalOS.

Imports and synchronizes all handwritten journal entries from journal_data.csv
into SQLite goalos.db daily_logs table with zero loss of information.

Parsing (PLAN time blocks, TASKS, AWAKE) is delegated to
JournalImportService so this script stays in sync with the shared,
tested logic instead of maintaining its own duplicate heuristics.
"""

import csv
import json
import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def parse_date(date_str: str) -> date:
    """Parse date from various string formats (D/M/YY, DD/MM/YYYY, YYYY-MM-DD)."""
    date_str = str(date_str).strip()
    if not date_str or date_str.lower() in ("nan", "none", ""):
        raise ValueError("Empty date string")

    # Try standard formats
    for fmt in ("%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            pass

    # Handle D/M/YY or D-M-YY with single digits
    parts = date_str.replace(".", "-").replace("/", "-").split("-")
    if len(parts) == 3:
        try:
            d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
            if y < 100:
                y += 2000
            return date(y, m, d)
        except ValueError:
            pass

    raise ValueError(f"Unrecognized date format: '{date_str}'")


def run_import(csv_path: str | None = None, db_path: str | None = None) -> int:
    """Read CSV and sync cleanly into SQLite daily_logs table."""
    from config.settings import settings
    from services.journal_import_service import JournalImportService

    if db_path is None:
        resolved_db = Path(settings.DB_PATH)
    else:
        resolved_db = Path(db_path)
        if not resolved_db.is_absolute():
            resolved_db = ROOT_DIR / db_path

    # Never substitute the fictional demo journal for a missing real one: that
    # would silently write demo rows into the user's own database.
    if csv_path is None:
        if settings.ENVIRONMENT.lower() == "demo":
            resolved_csv = ROOT_DIR / "data" / "demo_seed.csv"
        else:
            resolved_csv = ROOT_DIR / "data" / "Journal" / "journal_data.csv"
    else:
        resolved_csv = Path(csv_path)
        if not resolved_csv.is_absolute():
            resolved_csv = ROOT_DIR / csv_path

    if not resolved_csv.exists():
        print(f"Error: CSV file not found at {resolved_csv}")
        return 0

    svc = JournalImportService()
    conn = sqlite3.connect(str(resolved_db))
    conn.row_factory = sqlite3.Row

    with open(resolved_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0

        for row in reader:
            d_str = row.get("Date") or row.get("date")
            if not d_str:
                continue

            try:
                entry_date = parse_date(d_str)
            except Exception as exc:
                print(f"Skipping row with invalid date '{d_str}': {exc}")
                continue

            iso_date = entry_date.isoformat()

            gratitude = (row.get("Gratitude") or row.get("gratitude") or "").strip()
            plan_text = (row.get("Plan") or row.get("plan") or "").strip()
            tasks_raw = (row.get("Tasks") or row.get("tasks") or "").strip()
            review = (row.get("Review") or row.get("review") or row.get("journal_entry") or "").strip()
            takeaway = (row.get("Takeaway") or row.get("takeaway") or row.get("one_lesson") or "").strip()
            awake_text = (row.get("Awake") or row.get("AWAKE") or row.get("awake") or "").strip()

            # Bare-hour PLAN lines only resolve into a fixed hourly grid when an
            # AWAKE wake-hour is available to anchor them; otherwise keep the
            # raw parsed blocks as-is (see journal_import_service.py's
            # `_build_hourly_blocks` for the grid rule).
            plans = svc._parse_plans(plan_text)
            wake_hour = svc._parse_wake_hour(awake_text or None)
            if wake_hour is not None and plans:
                resolved = svc._resolve_plan_times(plans, wake_hour)
                plans = svc._build_hourly_blocks(resolved, wake_hour)
            time_blocks_json = json.dumps([b.model_dump() for b in plans])

            tasks = svc._parse_tasks(tasks_raw)
            planned_tasks_json = json.dumps([t.model_dump() for t in tasks]) if tasks else None
            completed_count = sum(1 for t in tasks if t.completed)
            completion_rate = round((completed_count / len(tasks)) * 100, 1) if tasks else 0.0

            awake_range = svc._parse_awake_range(awake_text or None)

            existing = conn.execute("SELECT id FROM daily_logs WHERE date = ?", (iso_date,)).fetchone()

            if existing:
                conn.execute("""
                    UPDATE daily_logs SET
                        gratitude = ?,
                        awake_range = ?,
                        time_blocks = ?,
                        planned_tasks = ?,
                        tasks_completed = ?,
                        task_completion_rate = ?,
                        journal_entry = ?,
                        takeaway = ?,
                        morning_completed = 1,
                        evening_completed = 1,
                        imported = 1,
                        import_source = 'journal_data.csv',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    gratitude,
                    awake_range,
                    time_blocks_json,
                    planned_tasks_json,
                    tasks_raw,
                    completion_rate,
                    review,
                    takeaway,
                    existing["id"],
                ))
            else:
                conn.execute("""
                    INSERT INTO daily_logs (
                        date, gratitude, awake_range, time_blocks, planned_tasks,
                        tasks_completed, task_completion_rate, journal_entry, takeaway,
                        morning_completed, evening_completed, imported, import_source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1, 1, 'journal_data.csv')
                """, (
                    iso_date,
                    gratitude,
                    awake_range,
                    time_blocks_json,
                    planned_tasks_json,
                    tasks_raw,
                    completion_rate,
                    review,
                    takeaway,
                ))

            count += 1

    # Sleep is last night's bedtime to today's wake-up, so it can only be derived once
    # every day is in; unknown (NULL) when the previous day has no AWAKE line.
    rows = conn.execute("SELECT id, date, awake_range, sleep_hours, imported FROM daily_logs").fetchall()
    sleep_by_date = svc.compute_sleep_series([(date.fromisoformat(r["date"]), r["awake_range"]) for r in rows])
    for r in rows:
        derived = sleep_by_date[date.fromisoformat(r["date"])]
        if r["imported"] and derived != r["sleep_hours"]:
            conn.execute("UPDATE daily_logs SET sleep_hours = ? WHERE id = ?", (derived, r["id"]))

    conn.commit()
    print(f"Successfully imported/synchronized {count} journal entries from {resolved_csv.name} into {resolved_db.name}!")
    conn.close()
    return count


if __name__ == "__main__":
    run_import()
