"""Journal parsing and stats — matches handwritten journal format."""

import json
import re
import uuid

from models.daily_log import DailyLog

_SORT_SEP = "\u2060"  # reserved


def ensure_task_ids(tasks: list[dict]) -> list[dict]:
  """Assign stable ids used by the UI and persisted in the task JSON."""
  for t in tasks:
    if not t.get("id"):
      t["id"] = uuid.uuid4().hex[:8]
  return tasks


def build_sort_labels(tasks: list[dict]) -> tuple[list[str], dict[str, str]]:
  """Build unique drag labels and map each label back to task id."""
  seen: dict[str, int] = {}
  labels: list[str] = []
  label_to_id: dict[str, str] = {}
  for t in tasks:
    preview = (t.get("text") or "").strip() or "New task"
    if len(preview) > 55:
      preview = preview[:52] + "..."
    base = f"⠿ {preview}"
    if base not in seen:
      seen[base] = 1
      label = base
    else:
      seen[base] += 1
      label = f"{base} ({seen[base]})"
    labels.append(label)
    label_to_id[label] = t["id"]
  return labels, label_to_id


def parse_tasks(text: str) -> list[dict]:
  """Parse numbered task lines; X / [done] marks completion."""
  tasks = []
  if not text or not text.strip():
    return tasks
  for i, line in enumerate(text.strip().split("\n"), 1):
    line = line.strip()
    if not line:
      continue
    completed = bool(re.search(r"\bX\b|\[done\]|✓|✔", line, re.IGNORECASE))
    cleaned = re.sub(r"^[①②③④⑤⑥⑦⑧⑨⑩\d]+[\.\)]\s*", "", line)
    cleaned = re.sub(r"\s*[\[X\]]\s*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+X\s*$", "", cleaned)
    cleaned = re.sub(r"\s*\[done\]\s*$", "", cleaned, flags=re.IGNORECASE)
    if cleaned:
      tasks.append({"text": cleaned.strip(), "completed": completed, "priority": i})
  return tasks


def normalize_tasks(tasks: list[dict]) -> list[dict]:
  """Ensure priority field; sort highest priority first (1 = top)."""
  normalized = []
  for i, t in enumerate(tasks):
    if not t.get("text", "").strip():
      continue
    task = {
      "id": str(t.get("id") or uuid.uuid4().hex[:8]),
      "text": t["text"].strip(),
      "completed": bool(t.get("completed")),
      "priority": int(t.get("priority") or i + 1),
    }
    if t.get("goal_id") is not None:
      task["goal_id"] = int(t["goal_id"])
    if t.get("milestone_id") is not None:
      task["milestone_id"] = int(t["milestone_id"])
    normalized.append(task)
  normalized.sort(key=lambda t: t["priority"])
  for i, t in enumerate(normalized, 1):
    t["priority"] = i
  return normalized


def validate_task_links(tasks: list[dict]) -> None:
  """Reject stale or cross-goal task references before they are persisted."""
  from database.connection import get_db

  with get_db() as conn:
    for task in tasks:
      goal_id = task.get("goal_id")
      milestone_id = task.get("milestone_id")
      if goal_id is not None and not conn.execute("SELECT 1 FROM goals WHERE id = ?", (goal_id,)).fetchone():
        raise ValueError(f"Task goal {goal_id} does not exist")
      if milestone_id is not None:
        milestone = conn.execute("SELECT goal_id FROM milestones WHERE id = ?", (milestone_id,)).fetchone()
        if not milestone:
          raise ValueError(f"Task milestone {milestone_id} does not exist")
        if goal_id is not None and milestone["goal_id"] != goal_id:
          raise ValueError("Task goal and milestone must be linked")


def load_tasks_from_log(log: DailyLog | None) -> list[dict]:
  """Load tasks from a daily log entry."""
  if not log:
    return []
  if log.planned_tasks:
    try:
      raw = json.loads(log.planned_tasks)
      if isinstance(raw, list):
        return normalize_tasks(raw)
    except json.JSONDecodeError:
      pass
  if log.tasks_completed:
    return normalize_tasks(parse_tasks(log.tasks_completed))
  return []


def pack_tasks(tasks: list[dict]) -> dict:
  """Prepare DB fields from structured task list."""
  ordered = normalize_tasks(tasks)
  return {
    "planned_tasks": json.dumps(ordered) if ordered else None,
    "tasks_completed": tasks_to_text(ordered) if ordered else None,
    "task_completion_rate": completion_rate(ordered),
  }


def tasks_to_text(tasks: list[dict]) -> str:
  """Format tasks back to journal style (priority order)."""
  lines = []
  for t in normalize_tasks(tasks):
    suffix = " X" if t.get("completed") else ""
    lines.append(f"{t['priority']}. {t['text']}{suffix}")
  return "\n".join(lines)


def parse_plans(text: str) -> list[dict]:
  """Parse time-blocked plans."""
  blocks = []
  pattern = re.compile(r"(\d{1,2}(?::\d{2})?)\s*[-–]\s*(\d{1,2}(?::\d{2})?)\s*:?\s*(.+)")
  for line in (text or "").strip().split("\n"):
    line = line.strip()
    if not line:
      continue
    match = pattern.match(line)
    if match:
      blocks.append({
        "start": match.group(1),
        "end": match.group(2),
        "activity": match.group(3).strip(),
      })
  return blocks


def completion_rate(tasks: list[dict]) -> float | None:
  if not tasks:
    return None
  done = sum(1 for t in tasks if t.get("completed"))
  return round(done / len(tasks) * 100, 1)


def log_task_stats(log: DailyLog) -> dict:
  """Task counts for a single day."""
  tasks = []
  if log.planned_tasks:
    try:
      tasks = json.loads(log.planned_tasks)
    except json.JSONDecodeError:
      tasks = parse_tasks(log.tasks_completed or log.planned_tasks or "")
  elif log.tasks_completed:
    tasks = parse_tasks(log.tasks_completed)
  total = len(tasks)
  done = sum(1 for t in tasks if t.get("completed"))
  rate = round(done / total * 100, 1) if total else None
  return {"total": total, "completed": done, "rate": rate}


def week_task_stats(logs: list[DailyLog]) -> dict:
  """Aggregate task completion across a week."""
  days_logged = len(logs)
  total_tasks = 0
  completed_tasks = 0
  daily_rates: list[float] = []
  for log in logs:
    stats = log_task_stats(log)
    total_tasks += stats["total"]
    completed_tasks += stats["completed"]
    if stats["rate"] is not None:
      daily_rates.append(stats["rate"])
  week_rate = round(completed_tasks / total_tasks * 100, 1) if total_tasks else None
  avg_daily_rate = round(sum(daily_rates) / len(daily_rates), 1) if daily_rates else None
  return {
    "days_logged": days_logged,
    "total_tasks": total_tasks,
    "completed_tasks": completed_tasks,
    "week_completion_rate": week_rate,
    "avg_daily_rate": avg_daily_rate,
  }


def serialize_journal_fields(
  gratitude: str,
  plans_text: str,
  tasks: list[dict] | str,
) -> dict:
  """Prepare DB fields from journal form."""
  if isinstance(tasks, str):
    task_list = parse_tasks(tasks)
  else:
    task_list = normalize_tasks(tasks)
  validate_task_links(task_list)
  plans = parse_plans(plans_text)
  packed = pack_tasks(task_list)
  return {
    "gratitude": gratitude or None,
    "time_blocks": json.dumps(plans) if plans else plans_text or None,
    **packed,
  }
