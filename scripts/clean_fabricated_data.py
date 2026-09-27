"""One-time cleanup: remove backfill-guessed wellness fields and downstream scores,
and repair the 3 task-blob rows caused by comma-joined notebook entries.

Run once, after `DataPortabilityService.create_backup()` has already produced a
backup (see backups/). Safe to re-run — every step is idempotent.
"""

import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def run(db_path: str = "goalos.db") -> None:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # --- 1. Null the six fabricated wellness fields on every row ---
    fields = ["sleep_hours", "sleep_quality", "energy_level", "mood_morning", "expected_focus", "deep_work_hours"]
    before = {}
    for f in fields:
        cur.execute(f"SELECT COUNT(*) FROM daily_logs WHERE {f} IS NOT NULL")
        before[f] = cur.fetchone()[0]

    cur.execute(f"UPDATE daily_logs SET {', '.join(f'{f} = NULL' for f in fields)}")
    print("Nulled fabricated fields, rows previously populated per field:", before)

    # --- 2. Delete the downstream score rows computed from those fabricated inputs ---
    cur.execute("SELECT COUNT(*) FROM scores WHERE scope='daily'")
    score_count = cur.fetchone()[0]
    cur.execute("DELETE FROM scores WHERE scope='daily'")
    print(f"Deleted {score_count} daily score rows (downstream of the fabricated fields).")

    # --- 3. Re-split the 3 real task-blob rows on their own embedded numbering ---
    blob_dates = ["2026-07-01", "2026-07-02", "2026-07-03"]
    for d in blob_dates:
        cur.execute("SELECT planned_tasks FROM daily_logs WHERE date=?", (d,))
        row = cur.fetchone()
        if not row or not row[0]:
            continue
        arr = json.loads(row[0])
        if not arr:
            continue
        raw_text = arr[0]["text"]
        parts = [p.strip().rstrip(".").strip() for p in re.split(r",\s*\d+\.\s*", raw_text) if p.strip()]
        task_objs = [
            {"id": f"t_{i+1}", "text": t, "completed": False, "priority": i + 1, "priority_tag": f"P{i+1}"}
            for i, t in enumerate(parts)
        ]
        new_planned = json.dumps(task_objs)
        new_tasks_completed = "\n".join(f"{i+1}. {t}" for i, t in enumerate(parts))
        new_top_priority = parts[0] if parts else None
        cur.execute(
            "UPDATE daily_logs SET planned_tasks=?, tasks_completed=?, task_completion_rate=0.0, top_priority=? WHERE date=?",
            (new_planned, new_tasks_completed, new_top_priority, d),
        )
        print(f"{d}: split into {len(parts)} tasks -> {parts}")

    conn.commit()
    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    run()
