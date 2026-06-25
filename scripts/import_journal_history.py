"""Import journal_history.json and transcribed markdown into GoalOS."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from database.migrations import run_migrations
from services.journal_import_service import JournalImportService

DATA_DIR = ROOT / "data"
JSON_PATH = DATA_DIR / "journal_history.json"
SUMMARY_PATH = DATA_DIR / "onboarding_summary.md"


def main() -> int:
  run_migrations()
  svc = JournalImportService()
  total_imported = 0
  total_memories = 0
  all_errors: list[str] = []

  if JSON_PATH.exists():
    print(f"Importing {JSON_PATH.name}...")
    result = svc.import_from_json(str(JSON_PATH))
    total_imported += result.successfully_imported
    total_memories += result.memories_extracted
    all_errors.extend(result.errors)
    print(
      f"  JSON: {result.successfully_imported} imported, "
      f"{result.skipped_duplicates} skipped, {len(result.errors)} errors"
    )
  else:
    print(f"Missing {JSON_PATH}")
    return 1

  summary = svc.generate_onboarding_summary()
  DATA_DIR.mkdir(parents=True, exist_ok=True)
  SUMMARY_PATH.write_text(summary, encoding="utf-8")

  print()
  print(f"Total: {total_imported} entries, {total_memories} memories")
  print(f"Summary saved to {SUMMARY_PATH}")
  print()
  print(summary)

  if all_errors:
    print()
    print(f"Errors ({len(all_errors)}):")
    for err in all_errors[:15]:
      print(f"  - {err}")
    if len(all_errors) > 15:
      print(f"  ... and {len(all_errors) - 15} more")

  return 0


if __name__ == "__main__":
  raise SystemExit(main())
