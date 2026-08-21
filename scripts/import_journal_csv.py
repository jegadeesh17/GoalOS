"""Robust Journal CSV Import Script for GoalOS.

Imports and synchronizes all handwritten journal entries from journal_data.csv
into SQLite goalos.db daily_logs table with zero loss of information.
"""

import csv
import json
import re
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
    parts = re.split(r"[/.-]", date_str)
    if len(parts) == 3:
        try:
            d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
            if y < 100:
                y += 2000
            return date(y, m, d)
        except ValueError:
            pass

    raise ValueError(f"Unrecognized date format: '{date_str}'")


def parse_tasks_from_text(tasks_text: str):
    """Parse task lines into structured JSON, formatted text, completion rate, and top priority."""
    if not tasks_text or not tasks_text.strip():
        return None, None, None, None

    lines = [line.strip() for line in tasks_text.strip().split("\n") if line.strip()]
    task_objs = []
    completed_count = 0
    top_priority_text = None

    for idx, line in enumerate(lines, 1):
        # Detect completion mark: (tick), ✓, ✔, [done], [x]
        is_completed = bool(re.search(r"\(tick\)|✓|✔|\[done\]|\[x\]", line, re.IGNORECASE))

        # Detect priority tag like P1, P2, P3 if present
        p_match = re.search(r"\b(P[1-5])\b", line, re.IGNORECASE)
        priority_tag = p_match.group(1).upper() if p_match else f"P{idx}"

        # Clean text
        cleaned = re.sub(r"^\d+[\.\)]\s*", "", line)  # Remove leading numbers
        cleaned = re.sub(r"\s*\((tick|x|~|\*)\)", "", cleaned, flags=re.IGNORECASE)  # Remove (tick)/(x)
        cleaned = re.sub(r"\s*\[(done|x| )\]", "", cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.strip()

        if idx == 1 and cleaned:
            top_priority_text = cleaned

        task_objs.append({
            "id": f"t_{idx}",
            "text": cleaned,
            "completed": is_completed,
            "priority": idx,
            "priority_tag": priority_tag,
        })

        if is_completed:
            completed_count += 1

    rate = round((completed_count / len(task_objs)) * 100, 1) if task_objs else 0.0
    return json.dumps(task_objs), tasks_text.strip(), rate, top_priority_text


def run_import(csv_path: str = "data/Journal/journal_data.csv", db_path: str = "goalos.db") -> int:
    """Read CSV and sync cleanly into SQLite daily_logs table."""
    resolved_csv = Path(csv_path)
    if not resolved_csv.is_absolute():
        resolved_csv = ROOT_DIR / csv_path

    resolved_db = Path(db_path)
    if not resolved_db.is_absolute():
        resolved_db = ROOT_DIR / db_path

    if not resolved_csv.exists():
        print(f"Error: CSV file not found at {resolved_csv}")
        return 0

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
            plan = (row.get("Plan") or row.get("plan") or "").strip()
            tasks_raw = (row.get("Tasks") or row.get("tasks") or "").strip()
            review = (row.get("Review") or row.get("review") or row.get("journal_entry") or "").strip()
            takeaway = (row.get("Takeaway") or row.get("takeaway") or row.get("one_lesson") or "").strip()

            planned_tasks_json, tasks_text, completion_rate, top_priority = parse_tasks_from_text(tasks_raw)

            existing = conn.execute("SELECT id, top_priority FROM daily_logs WHERE date = ?", (iso_date,)).fetchone()

            if existing:
                conn.execute("""
                    UPDATE daily_logs SET
                        gratitude = ?,
                        time_blocks = ?,
                        planned_tasks = ?,
                        tasks_completed = ?,
                        task_completion_rate = ?,
                        journal_entry = ?,
                        takeaway = ?,
                        one_lesson = ?,
                        top_priority = COALESCE(NULLIF(top_priority, ''), ?),
                        morning_completed = 1,
                        evening_completed = 1,
                        imported = 1,
                        import_source = 'journal_data.csv',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    gratitude,
                    plan,
                    planned_tasks_json,
                    tasks_text,
                    completion_rate,
                    review,
                    takeaway,
                    takeaway,
                    top_priority,
                    existing["id"],
                ))
            else:
                conn.execute("""
                    INSERT INTO daily_logs (
                        date, gratitude, time_blocks, planned_tasks, tasks_completed, task_completion_rate,
                        journal_entry, takeaway, one_lesson, top_priority, morning_completed, evening_completed,
                        imported, import_source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1, 1, 'journal_data.csv')
                """, (
                    iso_date,
                    gratitude,
                    plan,
                    planned_tasks_json,
                    tasks_text,
                    completion_rate,
                    review,
                    takeaway,
                    takeaway,
                    top_priority,
                ))

            count += 1

    conn.commit()
    print(f"Successfully imported/synchronized {count} journal entries from {resolved_csv.name} into {resolved_db.name}!")
    conn.close()
    return count


if __name__ == "__main__":
    run_import()
