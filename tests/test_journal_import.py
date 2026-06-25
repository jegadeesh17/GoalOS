"""Journal import service tests."""

from datetime import date

from services.journal_import_service import JournalImportService

SAMPLE_TEXT = """GRATITUDE    grateful for such friendly parents.
             23/6/26

PLANS
10:30-12     Restructuring Quandao planning app
1:30-3       Solve 10 Codekata Problems

TASKS
① Solve 10 Code Kata Problems          X
② Solve 10 Codekata                   X
③ Solve 10 Codekata
④ Prepare for evaluation              X

REVIEW       I did great work but not focusing on what matters

TAKEAWAY     Focus and lock in.
"""


class TestJournalImport:
  def test_parse_entry_from_dict(self, temp_db):
    svc = JournalImportService()
    entry = svc.parse_entry({
      "date": "23/6/26",
      "gratitude": "grateful for parents",
      "plans": "10:30-12: Restructuring app\n1:30-3: Solve problems",
      "tasks": "1. Solve 10 Codekata [done]\n2. Prepare evaluation X\n3. Review plan",
      "review": "Good day but not focused",
      "takeaway": "Focus and lock in",
    })
    assert entry.date == date(2026, 6, 23)
    assert len(entry.tasks) == 3
    assert entry.tasks[0].completed is True
    assert entry.task_completion_rate > 0

  def test_import_from_text_block(self, temp_db):
    svc = JournalImportService()
    result = svc.import_from_text_block(SAMPLE_TEXT)
    assert result.successfully_imported == 1
    assert result.memories_extracted > 0
    assert "Onboarding Summary" in result.onboarding_summary

  def test_parse_plans(self, temp_db):
    svc = JournalImportService()
    plans = svc._parse_plans("10:30-12: Restructuring app\n1:30-3: Solve problems")
    assert len(plans) == 2
    assert plans[0].activity == "Restructuring app"

  def test_parse_tasks_completion(self, temp_db):
    svc = JournalImportService()
    tasks = svc._parse_tasks("1. Task one X\n2. Task two [done]\n3. Task three")
    assert tasks[0].completed is True
    assert tasks[1].completed is True
    assert tasks[2].completed is False

  def test_date_formats(self, temp_db):
    svc = JournalImportService()
    assert svc._parse_date("23/6/26") == date(2026, 6, 23)
    assert svc._parse_date("2026-06-23") == date(2026, 6, 23)

  def test_duplicate_skip(self, temp_db):
    svc = JournalImportService()
    svc.import_from_text_block(SAMPLE_TEXT)
    result = svc.import_from_text_block(SAMPLE_TEXT)
    assert result.skipped_duplicates == 1

  def test_lesson_memory_from_review(self, temp_db):
    svc = JournalImportService()
    entry = svc.parse_entry({
      "date": "23/6/26",
      "review": "I did great but not focusing",
      "takeaway": "Focus more",
    })
    count = svc.store_entry(entry)
    assert count >= 1

  def test_import_from_json(self, temp_db, tmp_path):
    svc = JournalImportService()
    data = [
      {
        "date": "2/6/26",
        "gratitude": "grateful for parents",
        "plan": "10 - 12: Deep work",
        "tasks": "1. Solve codekata\n2. Gym",
        "review": "Good day",
        "takeaway": "Keep grinding",
      }
    ]
    path = tmp_path / "journal.json"
    path.write_text(__import__("json").dumps(data), encoding="utf-8")
    result = svc.import_from_json(str(path))
    assert result.successfully_imported == 1
    assert result.memories_extracted > 0

  def test_plan_column_alias(self, temp_db):
    svc = JournalImportService()
    entry = svc.parse_entry({
      "date": "3/6/26",
      "plan": "8 - 12: Study\n2 - 4: Codekata",
      "tasks": "1. Task one",
    })
    assert len(entry.plans) == 2

  def test_parse_plans_flexible_times(self, temp_db):
    svc = JournalImportService()
    plans = svc._parse_plans("7:15 - 9: Quandao project\n10 - 12: codekata")
    assert len(plans) == 2
    assert plans[0].activity == "Quandao project"
