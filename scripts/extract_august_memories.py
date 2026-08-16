"""Extract and index August 2026 journal memories into SQLite and ChromaDB."""
import os
import sys

sys.path.insert(0, os.path.abspath("."))

import json
from services.journal_import_service import JournalImportService
from database.connection import get_db

def run_extraction():
    service = JournalImportService()
    
    with open("data/Journal/august_2026_batch.json", "r", encoding="utf-8") as f:
        entries = json.load(f)
        
    print(f"Loaded {len(entries)} August 2026 entries for memory extraction...")
    
    total_memories = 0
    with get_db() as conn:
        for row in entries:
            parsed = service.parse_entry(row)
            # Find log_id for this date
            db_log = conn.execute("SELECT id FROM daily_logs WHERE date = ?", (parsed.date.isoformat(),)).fetchone()
            log_id = db_log["id"] if db_log else None
            
            # Extract memories
            memories_count = service._extract_memories(parsed, log_id)
            total_memories += memories_count
            print(f"[{parsed.date}] Extracted {memories_count} memories (log_id={log_id})")
            
    print(f"\nSuccessfully extracted and indexed {total_memories} memories into GoalOS!")

if __name__ == "__main__":
    run_extraction()
