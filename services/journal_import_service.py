"""Journal import service for Excel and handwritten text format."""

import json
import re
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from database.repositories.log_repository import LogRepository
from models.daily_log import DailyLogCreate
from models.import_result import ImportResult, ParsedEntry, ParsedTask, ParsedTimeBlock
from services.memory_service import MemoryService


VERBS = re.compile(
  r"^(focus|lock|start|finish|complete|do|run|study|learn|practice|build|write|read|solve)",
  re.IGNORECASE,
)


class JournalImportService:
  """Import historical journal entries from Excel or raw text."""

  def __init__(self):
    self.log_repo = LogRepository()
    self.memory_service = MemoryService()
    self._task_history: dict[str, int] = {}

  def import_from_excel(self, file_path: str) -> ImportResult:
    """Read Excel file and import all rows."""
    result = ImportResult()
    try:
      df = pd.read_excel(file_path)
    except Exception as e:
      result.errors.append(f"Failed to read Excel: {e}")
      return result

    required = {"date"}
    missing = required - set(df.columns.str.lower())
    if missing:
      result.errors.append(f"Missing columns: {missing}")
      return result

    df.columns = df.columns.str.lower().str.strip()
    dates: list[date] = []

    for idx, row in df.iterrows():
      result.total_entries += 1
      try:
        entry = self.parse_entry(row.to_dict())
        if self.log_repo.get_by_date(entry.date):
          result.skipped_duplicates += 1
          continue
        memories = self.store_entry(entry, source="excel")
        result.successfully_imported += 1
        result.memories_extracted += memories
        dates.append(entry.date)
      except Exception as e:
        result.errors.append(f"Row {idx + 2}: {e}")

    if dates:
      result.date_range = (min(dates), max(dates))
    result.onboarding_summary = self.generate_onboarding_summary()
    return result

  def import_from_json(self, file_path: str) -> ImportResult:
    """Read JSON array of journal entries and import each row."""
    result = ImportResult()
    try:
      rows = json.loads(Path(file_path).read_text(encoding="utf-8"))
    except Exception as e:
      result.errors.append(f"Failed to read JSON: {e}")
      return result

    if not isinstance(rows, list):
      result.errors.append("JSON must be an array of entry objects")
      return result

    dates: list[date] = []
    for idx, row in enumerate(rows):
      result.total_entries += 1
      if not isinstance(row, dict):
        result.errors.append(f"Row {idx + 1}: expected object, got {type(row).__name__}")
        continue
      try:
        entry = self.parse_entry(row)
        if self.log_repo.get_by_date(entry.date):
          result.skipped_duplicates += 1
          continue
        memories = self.store_entry(entry, source="json")
        result.successfully_imported += 1
        result.memories_extracted += memories
        dates.append(entry.date)
      except Exception as e:
        result.errors.append(f"Row {idx + 1}: {e}")

    if dates:
      result.date_range = (min(dates), max(dates))
    result.onboarding_summary = self.generate_onboarding_summary()
    return result

  def import_from_markdown(self, file_path: str) -> ImportResult:
    """Parse transcribed markdown journal files (Date/PLAN/TASKS/REVIEW/TAKEAWAY)."""
    result = ImportResult()
    try:
      text = Path(file_path).read_text(encoding="utf-8")
    except Exception as e:
      result.errors.append(f"Failed to read markdown: {e}")
      return result

    blocks = re.split(r"\n-{3,}\s*\n|\n={4,}\s*\n", text)
    dates: list[date] = []

    for idx, block in enumerate(blocks):
      block = block.strip()
      if not block:
        continue
      result.total_entries += 1
      try:
        row = self._parse_markdown_block(block)
        if not row:
          result.errors.append(f"Block {idx + 1}: no date found")
          continue
        entry = self.parse_entry(row)
        if self.log_repo.get_by_date(entry.date):
          result.skipped_duplicates += 1
          continue
        memories = self.store_entry(entry, source="markdown")
        result.successfully_imported += 1
        result.memories_extracted += memories
        dates.append(entry.date)
      except Exception as e:
        result.errors.append(f"Block {idx + 1}: {e}")

    if dates:
      result.date_range = (min(dates), max(dates))
    result.onboarding_summary = self.generate_onboarding_summary()
    return result

  def import_from_text_block(self, raw_text: str) -> ImportResult:
    """Parse raw pasted text in handwritten journal format."""
    result = ImportResult()
    entries = self._split_text_entries(raw_text)
    result.total_entries = len(entries)
    dates: list[date] = []

    for block in entries:
      try:
        entry = self._parse_text_block(block)
        if self.log_repo.get_by_date(entry.date):
          result.skipped_duplicates += 1
          continue
        memories = self.store_entry(entry, source="text")
        result.successfully_imported += 1
        result.memories_extracted += memories
        dates.append(entry.date)
      except Exception as e:
        result.errors.append(str(e))

    if dates:
      result.date_range = (min(dates), max(dates))
    result.onboarding_summary = self.generate_onboarding_summary()
    return result

  def parse_entry(self, row: dict) -> ParsedEntry:
    """Convert a raw row/dict into a structured ParsedEntry."""
    normalized = {str(k).lower().strip(): v for k, v in row.items()}
    entry_date = self._parse_date(str(normalized.get("date", "")))
    if not entry_date:
      raise ValueError(f"Invalid date: {normalized.get('date')}")

    plans_raw = normalized.get("plans") or normalized.get("plan") or ""
    plans = self._parse_plans(str(plans_raw or ""))
    tasks = self._parse_tasks(str(normalized.get("tasks", "") or ""))
    completed = sum(1 for t in tasks if t.completed)
    rate = completed / len(tasks) if tasks else 0.0

    return ParsedEntry(
      date=entry_date,
      gratitude=self._clean(normalized.get("gratitude")),
      plans=plans,
      tasks=tasks,
      review=self._clean(normalized.get("review")),
      takeaway=self._clean(normalized.get("takeaway")),
      task_completion_rate=rate,
    )

  def store_entry(self, entry: ParsedEntry, source: str = "import") -> int:
    """Store in daily_logs and extract memories."""
    time_blocks_json = json.dumps([b.model_dump() for b in entry.plans])
    tasks_json = json.dumps([t.model_dump() for t in entry.tasks])
    tasks_text = json.dumps([t.model_dump() for t in entry.tasks])

    log = DailyLogCreate(
      date=entry.date,
      gratitude=entry.gratitude,
      time_blocks=time_blocks_json,
      planned_tasks=tasks_json,
      tasks_completed=tasks_text,
      task_completion_rate=entry.task_completion_rate,
      journal_entry=entry.review,
      takeaway=entry.takeaway,
      one_lesson=entry.takeaway,
      evening_completed=bool(entry.review),
      imported=True,
      import_source=source,
      morning_ai_output=json.dumps([b.model_dump() for b in entry.plans]) if entry.plans else None,
    )
    stored = self.log_repo.upsert_by_date(log)
    return self._extract_memories(entry, stored.id)

  def generate_onboarding_summary(self) -> str:
    """Generate summary after import."""
    logs = self.log_repo.get_all()
    if not logs:
      return "No journal entries imported yet."

    total = len(logs)
    rates = [l.task_completion_rate for l in logs if l.task_completion_rate is not None]
    avg_rate = sum(rates) / len(rates) * 100 if rates else 0

    gratitudes = [l.gratitude for l in logs if l.gratitude]
    takeaways = [l.takeaway or l.one_lesson for l in logs if l.takeaway or l.one_lesson]
    tasks_all: list[str] = []
    for log in logs:
      if log.planned_tasks:
        try:
          for t in json.loads(log.planned_tasks):
            tasks_all.append(t.get("text", ""))
        except json.JSONDecodeError:
          pass

    gratitude_themes = self._top_themes(gratitudes, 3)
    task_themes = self._top_themes(tasks_all, 5)
    takeaway_themes = self._top_themes(takeaways, 3)

    dates = [l.date for l in logs]
    date_range = f"{min(dates)} to {max(dates)}"

    lines = [
      f"## Onboarding Summary",
      f"",
      f"**{total} days** imported ({date_range})",
      f"",
      f"**Task completion rate:** {avg_rate:.0f}%",
      f"",
      f"**Common gratitude themes:** {', '.join(gratitude_themes) or 'None detected'}",
      f"**Common task categories:** {', '.join(task_themes) or 'None detected'}",
      f"**Common takeaway themes:** {', '.join(takeaway_themes) or 'None detected'}",
    ]
    if avg_rate < 60:
      lines.append(f"\n*Pattern: You completed tasks at {avg_rate:.0f}% rate — room to improve consistency.*")
    elif avg_rate >= 75:
      lines.append(f"\n*Pattern: Strong execution at {avg_rate:.0f}% completion rate.*")

    return "\n".join(lines)

  def _extract_memories(self, entry: ParsedEntry, log_id: int) -> int:
    count = 0
    if entry.gratitude:
      self.memory_service.store(
        entry.gratitude, "achievement", 0.3, entry.date, "import", log_id
      )
      count += 1

    if entry.review:
      review_lower = entry.review.lower()
      if any(kw in review_lower for kw in ("but not", "however", "except")):
        self.memory_service.store(entry.review, "lesson", 0.8, entry.date, "import", log_id)
        count += 1
      self.memory_service.store(entry.review, "journal_insight", 0.6, entry.date, "import", log_id)
      count += 1

    if entry.takeaway:
      mem_type = "commitment" if VERBS.match(entry.takeaway.strip()) else "lesson"
      importance = 0.7
      self.memory_service.store(entry.takeaway, mem_type, importance, entry.date, "import", log_id)
      count += 1

    for task in entry.tasks:
      if not task.completed:
        key = task.text.lower().strip()
        self._task_history[key] = self._task_history.get(key, 0) + 1
        if self._task_history[key] >= 3:
          self.memory_service.store(
            f"Recurring uncompleted task: {task.text}",
            "distraction", 0.6, entry.date, "import", log_id,
          )
          count += 1

    return count

  def _parse_date(self, value: str) -> Optional[date]:
    value = str(value).strip()
    if not value or value.lower() == "nan":
      return None
    for fmt in ("%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
      try:
        return datetime.strptime(value, fmt).date()
      except ValueError:
        continue
  # Handle DD/M/YY
    parts = value.replace("-", "/").split("/")
    if len(parts) == 3:
      try:
        d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
        if y < 100:
          y += 2000
        return date(y, m, d)
      except ValueError:
        pass
    return None

  def _parse_plans(self, text: str) -> list[ParsedTimeBlock]:
    blocks = []
    pattern = re.compile(
      r"(\d{1,2}(?::\d{2})?)\s*[-–]\s*(\d{1,2}(?::\d{2})?)\s*:?\s*(.+)"
    )
    for line in text.strip().split("\n"):
      line = line.strip()
      if not line:
        continue
      match = pattern.match(line)
      if match:
        blocks.append(ParsedTimeBlock(
          start=match.group(1),
          end=match.group(2),
          activity=match.group(3).strip(),
        ))
    return blocks

  def _parse_markdown_block(self, block: str) -> Optional[dict]:
    """Extract journal fields from a transcribed markdown block."""
    entry_date = None
    date_match = re.search(r"Date:\s*(\d{1,2}/\d{1,2}/\d{2,4})", block, re.IGNORECASE)
    if date_match:
      entry_date = self._parse_date(date_match.group(1))
    if not entry_date:
      first_line = block.split("\n", 1)[0].strip()
      if re.match(r"^\d{1,2}/\d{1,2}/\d{2,4}$", first_line):
        entry_date = self._parse_date(first_line)
        block = block.split("\n", 1)[1] if "\n" in block else ""

    if not entry_date:
      for line in block.split("\n")[:5]:
        m = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4})", line)
        if m:
          entry_date = self._parse_date(m.group(1))
          if entry_date:
            break

    if not entry_date:
      return None

    sections: dict[str, str] = {}
    current = None
    section_headers = (
      "GRATITUDE", "PLAN", "PLANS", "TASKS", "TO DO", "TODO",
      "REVIEW", "ENDNOTE", "END NOTE", "TAKEAWAY",
    )
    for line in block.split("\n"):
      stripped = line.strip()
      if not stripped:
        if current:
          sections[current] += "\n"
        continue
      upper = stripped.upper()
      matched = None
      for header in section_headers:
        if upper == header or upper.startswith(header + ":") or upper.startswith(header + " "):
          matched = header
          remainder = re.sub(rf"^{re.escape(header)}\s*:?\s*", "", stripped, flags=re.IGNORECASE)
          current = header
          sections[current] = (remainder + "\n") if remainder else ""
          break
      if matched is None and current:
        sections[current] += line + "\n"

    plans = (
      sections.get("PLAN", "") + sections.get("PLANS", "")
    ).strip()
    tasks = (
      sections.get("TASKS", "") + sections.get("TO DO", "") + sections.get("TODO", "")
    ).strip()
    review = (
      sections.get("REVIEW", "") + sections.get("ENDNOTE", "") + sections.get("END NOTE", "")
    ).strip()
    takeaway = sections.get("TAKEAWAY", "").strip()
    takeaway = re.sub(r"^TAKEAWAY:\s*", "", takeaway, flags=re.IGNORECASE).strip()

    return {
      "date": entry_date.isoformat(),
      "gratitude": sections.get("GRATITUDE", "").strip() or None,
      "plans": plans or None,
      "tasks": tasks or None,
      "review": review or None,
      "takeaway": takeaway or None,
    }

  def _parse_tasks(self, text: str) -> list[ParsedTask]:
    tasks = []
    for line in text.strip().split("\n"):
      line = line.strip()
      if not line:
        continue
      completed = bool(re.search(r"\bX\b|\[done\]|✓|✔", line, re.IGNORECASE))
      cleaned = re.sub(r"^[①②③④⑤⑥⑦⑧⑨⑩\d]+[\.\)]\s*", "", line)
      cleaned = re.sub(r"\s*[\[X\]]\s*$", "", cleaned, flags=re.IGNORECASE)
      cleaned = re.sub(r"\s+X\s*$", "", cleaned)
      cleaned = re.sub(r"\s*\[done\]\s*$", "", cleaned, flags=re.IGNORECASE)
      if cleaned:
        tasks.append(ParsedTask(text=cleaned.strip(), completed=completed))
    return tasks

  def _split_text_entries(self, raw_text: str) -> list[str]:
    parts = re.split(r"(?=GRATITUDE\s)", raw_text, flags=re.IGNORECASE)
    return [p.strip() for p in parts if p.strip() and "GRATITUDE" in p.upper()[:20]]

  def _parse_text_block(self, block: str) -> ParsedEntry:
    sections: dict[str, str] = {}
    current = None
    section_names = ("GRATITUDE", "PLANS", "TASKS", "REVIEW", "TAKEAWAY")
    lines = block.split("\n")
    for line in lines:
      upper = line.strip().upper()
      matched = next((name for name in section_names if upper.startswith(name)), None)
      if matched:
        current = matched
        remainder = line.strip()[len(matched):].strip()
        sections[current] = (remainder + "\n") if remainder else ""
      elif current:
        sections[current] += line + "\n"

    entry_date = None
    for line in lines:
      date_match = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4})", line)
      if date_match:
        entry_date = self._parse_date(date_match.group(1))
        if entry_date:
          break

    if not entry_date:
      entry_date = date.today()

    row = {
      "date": entry_date.isoformat(),
      "gratitude": sections.get("GRATITUDE", "").strip(),
      "plans": sections.get("PLANS", "").strip(),
      "tasks": sections.get("TASKS", "").strip(),
      "review": sections.get("REVIEW", "").strip(),
      "takeaway": sections.get("TAKEAWAY", "").strip(),
    }
    return self.parse_entry(row)

  def _clean(self, value) -> Optional[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
      return None
    text = str(value).strip()
    if not text or text.lower() in ("nan", "(empty)", "empty"):
      return None
    return text

  def _top_themes(self, texts: list[str], n: int) -> list[str]:
    words: list[str] = []
    stop = {"the", "a", "an", "for", "and", "to", "of", "in", "on", "i", "my"}
    for text in texts:
      words.extend(w.lower() for w in re.findall(r"[a-zA-Z]{4,}", text) if w.lower() not in stop)
    return [w for w, _ in Counter(words).most_common(n)]
