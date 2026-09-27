"""One-time cleanup: delete all daily_logs (and their scores/memories) from
before 2026-07-01 - the date the final Gratitude/Awake/Plan/Tasks/Review/Takeaway
structure was adopted. Run only after a fresh DataPortabilityService backup.
"""

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CUTOVER_DATE = "2026-07-01"


def run(db_path: str = "goalos.db") -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT id FROM daily_logs WHERE date < ?", (CUTOVER_DATE,))
    log_ids = [r[0] for r in cur.fetchall()]
    print(f"Pre-standard daily_logs rows to delete: {len(log_ids)}")

    if not log_ids:
        print("Nothing to delete.")
        conn.close()
        return

    cur.execute("SELECT COUNT(*) FROM memories WHERE source_date < ?", (CUTOVER_DATE,))
    mem_count = cur.fetchone()[0]
    cur.execute("DELETE FROM memories WHERE source_date < ?", (CUTOVER_DATE,))
    print(f"Deleted {mem_count} memories sourced from those dates.")

    cur.execute("SELECT COUNT(*) FROM scores WHERE date < ?", (CUTOVER_DATE,))
    score_count = cur.fetchone()[0]
    cur.execute("DELETE FROM scores WHERE date < ?", (CUTOVER_DATE,))
    print(f"Deleted {score_count} score rows before {CUTOVER_DATE}.")

    cur.execute("DELETE FROM daily_logs WHERE date < ?", (CUTOVER_DATE,))
    print(f"Deleted {len(log_ids)} daily_logs rows before {CUTOVER_DATE}.")

    conn.commit()
    conn.close()
    print("\nDone. Remaining data starts at 2026-07-01, your confirmed standard structure.")


if __name__ == "__main__":
    run()
