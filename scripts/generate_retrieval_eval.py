"""Generate a deterministic retrieval report from committed synthetic fixtures."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import settings
from database.migrations import run_migrations
from services.memory_service import MemoryService, clear_collection_cache

REPORT = ROOT / "reports" / "evaluation.md"
FIXTURE = ROOT / "data" / "retrieval_eval.json"
SEED_MEMORIES = [
  ("Start the most important task before messages during the morning block.", "lesson", 0.9),
  ("Schedule exercise before evening fatigue to avoid skipping it after work.", "lesson", 0.8),
  ("A protected morning block improves focus and makes important work easier to start.", "journal_insight", 0.8),
]


def main() -> None:
  fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
  root = Path(tempfile.mkdtemp(prefix="goalos-retrieval-eval-"))
  old_db, old_chroma = settings.DB_PATH, settings.CHROMA_PATH
  try:
    settings.DB_PATH, settings.CHROMA_PATH = str(root / "eval.db"), str(root / "chroma")
    clear_collection_cache()
    run_migrations()
    memory = MemoryService()
    for text, memory_type, importance in SEED_MEMORIES:
      memory.store(text, memory_type, importance, date(2026, 1, 1), "synthetic_eval")
    lines = ["# GoalOS Memory Retrieval Evaluation", "", "Synthetic, deterministic evaluation. Scores are lexical expected-term matches over the top three results.", "", "| Query | Top result | Matched terms | Score |", "|---|---|---|---|"]
    scores = []
    for item in fixture:
      retrieved = memory.retrieve(item["query"], top_k=3)
      joined = " ".join(result.text.casefold() for result in retrieved)
      matched = [term for term in item["expected_terms"] if term.casefold() in joined]
      score = round(2 * len(matched) / len(item["expected_terms"]), 2)
      scores.append(score)
      top = retrieved[0].text[:90] if retrieved else "(none)"
      lines.append(f"| {item['query']} | {top} | {', '.join(matched) or 'none'} | {score:.2f} |")
    lines.extend(["", f"**Average retrieval relevance (0-2):** {sum(scores) / len(scores):.2f}", "", "Run: `python scripts/generate_retrieval_eval.py`."])
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT}")
  finally:
    clear_collection_cache()
    settings.DB_PATH, settings.CHROMA_PATH = old_db, old_chroma
    shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
  main()
