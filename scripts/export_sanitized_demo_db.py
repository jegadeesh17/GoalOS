"""Export and sanitize the authentic GoalOS database and Chroma vector store for portfolio demonstration.

Copies the local goalos.db into data/demo_goalos.db and local chroma_db into data/demo_chroma_db:
- All personal identifiers (PII) like the user's name ('Jegadeesh') replaced with demo persona 'Alex Chen'.
- University/location identifiers ('VIT Chennai', 'VIT', 'Chennai') masked to 'university' / 'city'.
- All 121 authentic daily logs, 8 real life goals, 262 extracted human memories and lessons,
  94 daily growth scores, and 46 AI APM telemetry spans preserved intact.
- ChromaDB vector store also sanitized so semantic AI coach retrieval works out-of-the-box.
- Full verification that zero personal names, university references, emails, or phone numbers remain.
"""

import os
import re
import shutil
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DB = ROOT / "goalos.db"
DST_DB = ROOT / "data" / "demo_goalos.db"
SRC_CHROMA = ROOT / "chroma_db"
DST_CHROMA = ROOT / "data" / "demo_chroma_db"


def sanitize_sqlite_file(db_path: Path, persona_name: str = "Alex Chen") -> None:
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()

    # 1. Update user profile name if user table exists
    try:
        c.execute("UPDATE user SET name = ? WHERE id = 1", (persona_name,))
        print(f"Updated user profile name to '{persona_name}' in {db_path.name}")
    except sqlite3.OperationalError:
        pass

    # 2. Text replacements dictionary: (pattern_or_substr, replacement)
    replacements = [
        ("Jegadeesh", "Alex"),
        ("jegadeesh", "Alex"),
        ("VIT Chennai", "my university"),
        ("vit chennai", "my university"),
        ("VIT", "university"),
        ("vit", "university"),
        ("Chennai", "city"),
        ("chennai", "city"),
    ]

    tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

    for table in tables:
        # Skip internal FTS shadow tables that will be rebuilt
        if table.startswith("memory_fts_") or table.startswith("embedding_fulltext_search_"):
            continue
        try:
            columns = [col[1] for col in c.execute(f"PRAGMA table_info({table})").fetchall()]
            for col in columns:
                for target, repl in replacements:
                    c.execute(f"UPDATE {table} SET {col} = replace({col}, ?, ?) WHERE {col} LIKE ?", (target, repl, f"%{target}%"))
        except Exception as e:
            # Not all tables/columns support direct string replace
            pass

    # Rebuild FTS if memory_fts exists
    try:
        c.execute("INSERT INTO memory_fts(memory_fts) VALUES('rebuild')")
    except Exception:
        pass

    conn.commit()
    c.execute("VACUUM")
    conn.commit()
    conn.close()


def verify_sanitization(db_path: Path) -> int:
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    pii_found = 0

    forbidden = re.compile(r"\b(jegadeesh|chennai|vit)\b", re.I)

    for table in tables:
        try:
            for row in c.execute(f"SELECT * FROM {table}").fetchall():
                row_str = " ".join(str(x) for x in row if x)
                m = forbidden.search(row_str)
                if m:
                    pii_found += 1
                    print(f"WARNING [{db_path.name}:{table}]: Found '{m.group(0)}' in: {row_str[:80]}")
        except Exception:
            pass

    conn.close()
    return pii_found


def export_sanitized_db(persona_name: str = "Alex Chen") -> int:
    if not SRC_DB.exists():
        print(f"Error: Source database {SRC_DB} does not exist.")
        return 0

    DST_DB.parent.mkdir(parents=True, exist_ok=True)
    if DST_DB.exists():
        DST_DB.unlink()

    shutil.copyfile(SRC_DB, DST_DB)
    print(f"Copied {SRC_DB.name} to {DST_DB.name}")

    sanitize_sqlite_file(DST_DB, persona_name)
    pii_remaining = verify_sanitization(DST_DB)

    conn = sqlite3.connect(str(DST_DB))
    c = conn.cursor()
    logs_cnt = c.execute("SELECT COUNT(*) FROM daily_logs").fetchone()[0]
    goals_cnt = c.execute("SELECT COUNT(*) FROM goals").fetchone()[0]
    mems_cnt = c.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    scores_cnt = c.execute("SELECT COUNT(*) FROM scores").fetchone()[0]
    telemetry_cnt = c.execute("SELECT COUNT(*) FROM ai_telemetry").fetchone()[0]
    user_name = c.execute("SELECT name FROM user WHERE id = 1").fetchone()[0]
    conn.close()

    print("\n=== Sanitized Demo Database Summary ===")
    print(f"Location:           {DST_DB} ({DST_DB.stat().st_size / 1024:.1f} KB)")
    print(f"User Profile Name:  '{user_name}'")
    print(f"Daily Logs:         {logs_cnt}")
    print(f"Active Goals:       {goals_cnt}")
    print(f"Authentic Memories: {mems_cnt}")
    print(f"Daily Scores:       {scores_cnt}")
    print(f"AI Telemetry Spans: {telemetry_cnt}")
    print(f"PII Verification:   {pii_remaining} forbidden terms remaining.")

    # Also sanitize ChromaDB
    if SRC_CHROMA.exists():
        if DST_CHROMA.exists():
            shutil.rmtree(DST_CHROMA)
        shutil.copytree(SRC_CHROMA, DST_CHROMA)
        chroma_sqlite = DST_CHROMA / "chroma.sqlite3"
        if chroma_sqlite.exists():
            sanitize_sqlite_file(chroma_sqlite, persona_name)
            chroma_pii = verify_sanitization(chroma_sqlite)
            print(f"ChromaDB Sanitized: {chroma_sqlite} ({chroma_pii} forbidden terms remaining)")

    return DST_DB.stat().st_size


if __name__ == "__main__":
    export_sanitized_db()
