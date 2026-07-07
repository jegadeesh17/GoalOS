"""Generate memory retrieval evaluation report."""

from __future__ import annotations

import csv
import os
import sys
from datetime import date

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from services.memory_service import MemoryService

TEMPLATE = os.path.join(ROOT, "docs", "goalos_eval_template.csv")
REPORT = os.path.join(ROOT, "reports", "evaluation.md")

SEED_MEMORIES = [
    ("I delayed deep work because meetings ran long.", "journal_insight", 0.8),
    ("Skipped workout after office three days this week.", "journal_insight", 0.7),
    ("Missed SQL practice commitment on Tuesday.", "commitment", 0.9),
    ("Long-term goals not moving despite busy days.", "journal_insight", 0.75),
    ("Pattern: late-night scrolling hurts morning focus.", "journal_insight", 0.85),
]


def _load_queries() -> list[dict]:
    rows = []
    with open(TEMPLATE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def _score_hit(query: str, expected_focus: str, memories: list) -> tuple[str, float]:
    if not memories:
        return "miss", 0.0
    joined = " ".join(m.text.lower() for m in memories[:3])
    focus_tokens = expected_focus.lower().split()
    hits = sum(1 for token in focus_tokens if token in joined or token in query.lower())
    if hits >= 2 or expected_focus.lower() in joined:
        return "hit", 2.0
    if hits == 1:
        return "partial", 1.0
    return "miss", 0.0


def main() -> None:
    memory = MemoryService()
    if memory.count() < 3:
        for text, mem_type, importance in SEED_MEMORIES:
            memory.store(text, mem_type, importance=importance, source_date=date.today())

    queries = _load_queries()
    lines = [
        "# GoalOS — Memory Retrieval Evaluation",
        "",
        "Manual 5-query retrieval check using composite ranking (40% semantic, 30% importance, 20% recency, 10% frequency).",
        "",
        "| Query ID | Query | Expected Focus | Top Memory | Result | Score |",
        "|----------|-------|----------------|------------|--------|-------|",
    ]
    scores = []
    for row in queries:
        retrieved = memory.retrieve(row["query_text"], top_k=3)
        top_text = retrieved[0].text[:80] + "..." if retrieved else "(none)"
        result, score = _score_hit(row["query_text"], row["expected_focus"], retrieved)
        scores.append(score)
        lines.append(
            f"| {row['query_id']} | {row['query_text'][:50]}... | {row['expected_focus']} | {top_text} | {result} | {score} |"
        )

    avg = sum(scores) / len(scores) if scores else 0
    lines.extend(
        [
            "",
            f"**Average retrieval relevance (0–2):** {avg:.2f}",
            "",
            "## Notes",
            "- Seeded demo memories used when corpus is sparse; replace with your journal import for production eval.",
            "- Regenerate: `python scripts/generate_retrieval_eval.py`",
        ]
    )
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
