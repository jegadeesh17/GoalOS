"""Curate and sanitize a 14-day authentic slice of journal entries for public demo.

Extracts real engineering, coding, and productivity logs while redacting
any personal names, private contacts, or sensitive personal identifiers.
Outputs to data/demo_seed.csv which is safe for public demo and repository seeding.
"""

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT_CSV = ROOT / "data" / "Journal" / "journal_data.csv"
OUTPUT_CSV = ROOT / "data" / "demo_seed.csv"

# Redaction patterns for personal privacy
REDACTIONS = [
    (r"\bvisit uncle\b", "family check-in"),
    (r"\bwash clothes\b", "personal chores"),
    (r"\bFold all clothes\b", "evening reset"),
    (r"\blings office\b", "coworking workspace"),
    (r"\bEndpoint clinical\b", "Technical Interview Prep"),
    (r"\bQuandao\b", "Quant Platform"),
    (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}", "[email-redacted]"),
    (r"\b\+?91[-\s]?[6-9]\d{9}\b", "[phone-redacted]"),
]


def sanitize_text(text: str) -> str:
    if not text:
        return ""
    result = text
    for pattern, replacement in REDACTIONS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result.strip()


def export_slice(max_days: int = 14) -> int:
    if not INPUT_CSV.exists():
        print(f"Error: {INPUT_CSV} not found.")
        return 0

    rows = []
    with open(INPUT_CSV, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            d_str = row.get("Date") or row.get("date") or ""
            tasks = row.get("Tasks") or row.get("tasks") or ""
            review = row.get("Review") or row.get("review") or ""
            plan = row.get("Plan") or row.get("plan") or ""
            gratitude = row.get("Gratitude") or row.get("gratitude") or ""
            takeaway = row.get("Takeaway") or row.get("takeaway") or ""

            # Filter for meaningful entries with substantial tasks & reflections
            if d_str and (len(tasks) > 25 or len(review) > 20):
                rows.append({
                    "Date": d_str.strip(),
                    "Gratitude": sanitize_text(gratitude),
                    "Plan": sanitize_text(plan),
                    "Tasks": sanitize_text(tasks),
                    "Review": sanitize_text(review),
                    "Takeaway": sanitize_text(takeaway),
                })

    # Pick 14 diverse, high-signal engineering days
    curated = rows[:max_days] if len(rows) >= max_days else rows

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["Date", "Gratitude", "Plan", "Tasks", "Review", "Takeaway"]

    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(curated)

    print(f" Successfully exported {len(curated)} curated, sanitized days to {OUTPUT_CSV}")
    return len(curated)


if __name__ == "__main__":
    export_slice()
