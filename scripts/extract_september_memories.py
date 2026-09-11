"""Extract and index September 2026 journal memories into SQLite and ChromaDB."""
import os
import sys

sys.path.insert(0, os.path.abspath("."))

import json

from database.connection import get_db
from services.journal_import_service import JournalImportService


def run_extraction():
    service = JournalImportService()
    
    with open("data/Journal/september_2026_batch.json", "r", encoding="utf-8") as f:
        entries = json.load(f)
        
    print(f"Loaded {len(entries)} September 2026 entries for memory extraction...")
    
    # Pre-fetch all daily log IDs to avoid holding a SQLite transaction open
    with get_db() as conn:
        rows = conn.execute("SELECT id, date FROM daily_logs WHERE date >= '2026-09-01'").fetchall()
        date_to_id = {r["date"]: r["id"] for r in rows}
    
    print(f"Found {len(date_to_id)} daily_logs records for September 2026.")
    
    total_memories = 0
    for row in entries:
        parsed = service.parse_entry(row)
        log_id = date_to_id.get(parsed.date.isoformat())
        
        # Extract and store memories (each memory stores via isolated get_db context)
        memories_count = service._extract_memories(parsed, log_id)
        total_memories += memories_count
        print(f"[{parsed.date}] Extracted {memories_count} memories (log_id={log_id})")
        
    print(f"\nSuccessfully extracted and indexed {total_memories} memories into GoalOS!")


if __name__ == "__main__":
    run_extraction()
