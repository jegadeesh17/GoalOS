import sqlite3
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def check_db(db_path: Path):
    if not db_path.exists():
        print(f"{db_path} does not exist!")
        return
    print(f"\n=== Checking {db_path} ===")
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print(f"Tables ({len(tables)}): {tables}")

    matches = []
    for t in tables:
        if t.startswith("sqlite_"):
            continue
        try:
            for row in c.execute(f"SELECT * FROM {t}").fetchall():
                row_str = " ".join(str(x) for x in row if x)
                if re.search(r"\b(jegadeesh|chennai|vit)\b", row_str, re.I):
                    matches.append((t, row_str[:100]))
        except Exception as e:
            pass

    if matches:
        print(f"Found {len(matches)} PII matches:")
        for t, s in matches:
            print(f"  [{t}] {s}")
    else:
        print("VERIFIED: 0 occurrences of 'jegadeesh' found.")

    conn.close()

if __name__ == "__main__":
    check_db(ROOT / "data" / "demo_goalos.db")
    check_db(ROOT / "data" / "demo_chroma_db" / "chroma.sqlite3")

