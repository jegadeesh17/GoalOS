"""Fix import_journal_csv.py to cleanly populate goalos.db from journal_data.csv."""
import csv
import re
import sqlite3
from datetime import date

def parse_date(date_str: str) -> date:
    parts = date_str.strip().split('/')
    if len(parts) == 3:
        day = int(parts[0])
        month = int(parts[1])
        year = int(parts[2])
        if year < 100:
            year += 2000
        return date(year, month, day)
    raise ValueError(f"Unrecognized date format: {date_str}")

def parse_tasks_from_text(tasks_text: str):
    import json
    if not tasks_text or not tasks_text.strip():
        return None, None, None
    
    lines = [l.strip() for l in tasks_text.strip().split('\n') if l.strip()]
    task_objs = []
    completed_count = 0
    
    for idx, line in enumerate(lines, 1):
        is_completed = bool(re.search(r'\(tick\)|✓|✔|\[done\]', line, re.IGNORECASE))
        cleaned = re.sub(r'^\d+[\.\)]\s*', '', line)
        cleaned = re.sub(r'\s*\((tick|x|~|\*)\)', '', cleaned, flags=re.IGNORECASE).strip()
        
        task_objs.append({
            "id": f"t_{idx}",
            "text": cleaned,
            "completed": is_completed,
            "priority": idx
        })
        if is_completed:
            completed_count += 1
            
    rate = round((completed_count / len(task_objs)) * 100, 1) if task_objs else 0.0
    return json.dumps(task_objs), tasks_text, rate

def run_import():
    conn = sqlite3.connect("goalos.db")
    conn.row_factory = sqlite3.Row
    
    with open("data/Journal/journal_data.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            d_str = row.get("Date") or row.get("date")
            if not d_str:
                continue
            try:
                entry_date = parse_date(d_str)
            except Exception:
                continue
                
            iso_date = entry_date.isoformat()
            
            gratitude = (row.get("Gratitude") or row.get("gratitude") or "").strip()
            plan = (row.get("Plan") or row.get("plan") or "").strip()
            tasks_raw = (row.get("Tasks") or row.get("tasks") or "").strip()
            review = (row.get("Review") or row.get("review") or row.get("journal_entry") or "").strip()
            takeaway = (row.get("Takeaway") or row.get("takeaway") or row.get("one_lesson") or "").strip()
            
            planned_tasks_json, tasks_text, completion_rate = parse_tasks_from_text(tasks_raw)
            
            existing = conn.execute("SELECT id FROM daily_logs WHERE date = ?", (iso_date,)).fetchone()
            
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
                        morning_completed = 1,
                        evening_completed = 1,
                        imported = 1,
                        import_source = 'journal_data.csv',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (gratitude, plan, planned_tasks_json, tasks_text, completion_rate, review, takeaway, takeaway, existing["id"]))
            else:
                conn.execute("""
                    INSERT INTO daily_logs (
                        date, gratitude, time_blocks, planned_tasks, tasks_completed, task_completion_rate,
                        journal_entry, takeaway, one_lesson, morning_completed, evening_completed, imported, import_source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1, 1, 'journal_data.csv')
                """, (iso_date, gratitude, plan, planned_tasks_json, tasks_text, completion_rate, review, takeaway, takeaway))
            count += 1
            
    conn.commit()
    print(f"Successfully imported/updated {count} journal entries into goalos.db!")
    conn.close()

if __name__ == "__main__":
    run_import()
