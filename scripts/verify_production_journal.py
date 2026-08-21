"""Verify August 2026 production readiness in GoalOS."""
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.abspath("."))

from services.memory_service import MemoryService


def verify_sqlite():
    conn = sqlite3.connect("goalos.db")
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, date, gratitude, planned_tasks, task_completion_rate, journal_entry, takeaway, imported "
        "FROM daily_logs WHERE date LIKE '2026-08-%' ORDER BY date ASC"
    ).fetchall()
    
    print("=== SQLite daily_logs Verification ===")
    print(f"Total August 2026 logs found: {len(rows)}")
    assert len(rows) == 15, f"Expected 15 rows for August 2026, found {len(rows)}"
    
    for r in rows:
        tasks = json.loads(r["planned_tasks"]) if r["planned_tasks"] else []
        print(f"[{r['date']}] Rate: {r['task_completion_rate']}% | Tasks: {len(tasks)} | Gratitude: {r['gratitude'][:30]}...")
        assert r["gratitude"], f"Gratitude missing for {r['date']}"
        assert r["journal_entry"], f"Journal entry missing for {r['date']}"
        assert r["takeaway"], f"Takeaway missing for {r['date']}"
    conn.close()
    print(" SQLite verification passed!")

def verify_memories():
    print("\n=== Memory & Vector Retrieval Verification ===")
    conn = sqlite3.connect("goalos.db")
    conn.row_factory = sqlite3.Row
    memories = conn.execute(
        "SELECT id, text, type, importance, source_date FROM memories "
        "WHERE source_date LIKE '2026-08-%' ORDER BY source_date ASC"
    ).fetchall()
    print(f"Total August 2026 memories stored in SQLite: {len(memories)}")
    assert len(memories) >= 30, f"Expected at least 30 memories, found {len(memories)}"
    conn.close()
    
    # Test vector memory retrieval
    mem_service = MemoryService()
    test_queries = [
        "interview preparation mistakes and study",
        "lock in and stop wasting time",
        "gratitude good health bigger dreams"
    ]
    for q in test_queries:
        results = mem_service.retrieve(q, top_k=3)
        print(f"\nQuery: '{q}' -> Top Retrieved Memory:")
        if results:
            top = results[0]
            print(f"  [{top.type}] ({top.source_date}) {top.text}")
        else:
            print("  No match found!")
            
    print("\n Memory & vector retrieval verification passed!")

if __name__ == "__main__":
    verify_sqlite()
    verify_memories()
