"""Extract and index July 2026 journal memories into SQLite and ChromaDB."""
import os
import sys

sys.path.insert(0, os.path.abspath("."))

from database.connection import get_db
from services.journal_import_service import JournalImportService


def run_extraction():
    service = JournalImportService()
    
    with get_db() as conn:
        # Fetch July 2026 logs that have journal_entry or takeaway
        rows = conn.execute(
            "SELECT * FROM daily_logs WHERE date LIKE '2026-07-%' ORDER BY date ASC"
        ).fetchall()
        
        print(f"Loaded {len(rows)} July 2026 daily logs for memory indexing...")
        
        # Check existing July memories count
        existing_mem_count = conn.execute(
            "SELECT count(*) FROM memories WHERE source_date LIKE '2026-07-%'"
        ).fetchone()[0]
        print(f"Existing July memories before indexing: {existing_mem_count}")
        
        total_extracted = 0
        for r in rows:
            dict_row = dict(r)
            # Create a parsed entry from the row
            parsed = service.parse_entry({
                "date": dict_row["date"],
                "gratitude": dict_row["gratitude"],
                "plans": dict_row["time_blocks"],
                "tasks": dict_row["tasks_completed"],
                "review": dict_row["journal_entry"],
                "takeaway": dict_row["takeaway"] or dict_row["one_lesson"],
            })
            
            count = service._extract_memories(parsed, dict_row["id"])
            total_extracted += count
            
        print(f"\nExtracted and indexed {total_extracted} memories for July 2026!")
        
        new_total = conn.execute("SELECT count(*) FROM memories").fetchone()[0]
        print(f"Total memories now stored in GoalOS: {new_total}")

if __name__ == "__main__":
    run_extraction()
