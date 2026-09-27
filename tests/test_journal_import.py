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

  def test_parse_awake_range_computes_sleep_hours(self, temp_db):
    svc = JournalImportService()
    awake_range, sleep_hours = svc._parse_awake_range("9:00 AM - 12.30 AM.")
    assert awake_range == "9:00 AM - 12.30 AM"
    assert sleep_hours == 8.5

  def test_parse_awake_range_unparseable_does_not_guess(self, temp_db):
    svc = JournalImportService()
    awake_range, sleep_hours = svc._parse_awake_range("woke up late")
    assert awake_range == "woke up late"
    assert sleep_hours is None

  def test_parse_awake_range_empty(self, temp_db):
    svc = JournalImportService()
    assert svc._parse_awake_range("") == (None, None)
    assert svc._parse_awake_range(None) == (None, None)

  def test_parse_entry_includes_awake_section(self, temp_db):
    svc = JournalImportService()
    entry = svc.parse_entry({
      "date": "19/9/26",
      "gratitude": "I am grateful for having good friends",
      "awake": "9:00 AM - 12.30 AM.",
      "plan": "9-10: Wakeup, shower, breakfast, job application",
      "tasks": "1. Apply for few companies ✓\n2. Study for the interview X",
      "review": "I am not focused at all",
      "takeaway": "I am gonna regret very much.",
    })
    assert entry.awake_range == "9:00 AM - 12.30 AM"
    assert entry.sleep_hours == 8.5

  def test_markdown_block_parses_awake_section(self, temp_db):
    svc = JournalImportService()
    text = """19/9/26
GRATITUDE
I am grateful for having good friends

AWAKE
9:00 AM - 12.30 AM.

PLAN
9-10 Wakeup, shower, breakfast, job application
10-11 Tea time break, applications

TASKS
① Apply for few companies ✓
② Study for the interview X
③ Wash clothes ✓

REVIEW
I am not focused at all

TAKEAWAY
I am gonna regret very much.
"""
    row = svc._parse_markdown_block(text)
    assert row["awake"] == "9:00 AM - 12.30 AM."
    entry = svc.parse_entry(row)
    assert entry.sleep_hours == 8.5
    assert len(entry.tasks) == 3
    assert entry.tasks[0].completed is True
    assert entry.tasks[1].completed is True
    assert entry.tasks[2].completed is True

  def test_hourly_plan_grid_matches_worked_example(self, temp_db):
    svc = JournalImportService()
    plan_text = "\n".join([
      "9-10   Wakeup, shower, breakfast, job application",
      "10-11  Tea time break, applications",
      "11-12  applications, chill",
      "12-1   lunch and youtube",
      "1-3    chess and networking",
      "3-4    chill",
      "4-7    timewasted",
      "7-8    dinner & youtube",
      "8-12   time waste",
    ])
    entry = svc.parse_entry({
      "date": "27/9/26",
      "awake": "9:00 AM - 12.30 AM.",
      "plan": plan_text,
    })
    assert len(entry.plans) == 15  # hours 9 through 23 inclusive
    assert entry.plans[0].start == "9"
    assert entry.plans[0].end == "10"
    assert entry.plans[0].activity == "Wakeup, shower, breakfast, job application"
    assert entry.plans[-1].start == "23"
    assert entry.plans[-1].end == "24"
    assert entry.plans[-1].activity == "time waste"
    expected_activities = [
      "Wakeup, shower, breakfast, job application",  # 9-10
      "Tea time break, applications",  # 10-11
      "applications, chill",  # 11-12
      "lunch and youtube",  # 12-13
      "chess and networking",  # 13-14
      "chess and networking",  # 14-15
      "chill",  # 15-16
      "timewasted",  # 16-17
      "timewasted",  # 17-18
      "timewasted",  # 18-19
      "dinner & youtube",  # 19-20
      "time waste",  # 20-21
      "time waste",  # 21-22
      "time waste",  # 22-23
      "time waste",  # 23-24
    ]
    assert [b.activity for b in entry.plans] == expected_activities

  def test_hourly_plan_grid_repeats_activity_across_multi_hour_block(self, temp_db):
    svc = JournalImportService()
    entry = svc.parse_entry({
      "date": "27/9/26",
      "awake": "6:00 AM - 11:00 PM.",
      "plan": "6-9 met my friends",
    })
    assert len(entry.plans) == 18  # hours 6 through 23
    first_three = entry.plans[:3]
    assert [b.start for b in first_three] == ["6", "7", "8"]
    assert all(b.activity == "met my friends" for b in first_three)

  def test_hourly_plan_grid_leaves_gap_hour_empty(self, temp_db):
    svc = JournalImportService()
    plan_text = "9-10 applications\n11-12 chill"
    entry = svc.parse_entry({
      "date": "27/9/26",
      "awake": "9:00 AM - 11:00 PM.",
      "plan": plan_text,
    })
    by_start = {b.start: b for b in entry.plans}
    assert by_start["9"].activity == "applications"
    assert by_start["10"].activity == ""
    assert by_start["11"].activity == "chill"

  def test_no_awake_section_falls_back_to_raw_plan_blocks(self, temp_db):
    svc = JournalImportService()
    entry = svc.parse_entry({
      "date": "27/9/26",
      "plan": "10:30-12: Restructuring app\n1:30-3: Solve problems",
    })
    assert len(entry.plans) == 2
    assert entry.plans[0].start == "10:30"
    assert entry.plans[0].activity == "Restructuring app"

  def test_store_entry_persists_awake_and_sleep(self, temp_db):
    svc = JournalImportService()
    entry = svc.parse_entry({
      "date": "20/9/26",
      "gratitude": "grateful",
      "awake": "9:00 AM - 12.30 AM.",
      "review": "fine",
    })
    svc.store_entry(entry)
    log = svc.log_repo.get_by_date(date(2026, 9, 20))
    assert log.awake_range == "9:00 AM - 12.30 AM"
    assert log.sleep_hours == 8.5
