"""Link journal tasks to goals so goal alignment can be measured from real decisions, not word overlap.

A task is identified by the key of its wording (`journal_helpers.task_key`). Its goal is the first hit of:
1. an explicit link the user saved (a goal, or "none" = reviewed, serves no goal),
2. a unique match on the goals' user-written cues,
3. otherwise it is *unreviewed*: unknown, never counted as misaligned.
Everything here is deterministic and local; no task text leaves the machine.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Callable, Literal, Optional

from database.repositories.goal_repository import GoalRepository
from database.repositories.log_repository import LogRepository
from database.repositories.task_link_repository import TaskLinkRepository
from models.goal import Goal
from models.task_link import TaskLink, TaskLinkWrite
from services.journal_helpers import planned_task_list, task_key


@dataclass(frozen=True)
class Resolution:
  kind: Literal["goal", "none", "unreviewed"]
  goal_id: Optional[int] = None


UNREVIEWED = Resolution("unreviewed")
NO_GOAL = Resolution("none")


def cue_matches(cue: str, key: str) -> bool:
  """A one-word cue is a prefix of any word of the task (`appl` matches `applications`); a multi-word cue
  must appear as whole words. Cues are already normalised like keys."""
  if not cue or not key:
    return False
  if " " in cue:
    return f" {cue} " in f" {key} "
  return any(token.startswith(cue) for token in key.split())


def resolve_key(key: str, links: dict[str, TaskLink], goals: list[Goal]) -> Resolution:
  link = links.get(key)
  if link is not None:
    return NO_GOAL if link.kind == "none" else Resolution("goal", link.goal_id)
  matched = {
    goal.id for goal in goals if goal.status == "active" and any(cue_matches(cue, key) for cue in goal.cues or [])
  }
  if len(matched) == 1:
    return Resolution("goal", next(iter(matched)))
  return UNREVIEWED  # no cue hit, or several goals claim it


def completed_texts(log) -> list[str]:
  """Wording of the tasks ticked on a day, from the task list only (a log without one has unknown tasks)."""
  return [str(t["text"]).strip() for t in planned_task_list(log) if t.get("completed")]


class TaskLinkService:
  """Resolve tasks to goals, hold the review queue, and report how much attention each goal got."""

  def __init__(self) -> None:
    self.log_repo = LogRepository()
    self.goal_repo = GoalRepository()
    self.link_repo = TaskLinkRepository()

  def resolver(self, goals: Optional[list[Goal]] = None) -> Callable[[str], Resolution]:
    """task text -> Resolution, with links and goals read once (callers score many days in a row)."""
    goals = self.goal_repo.get_active() if goals is None else goals
    links = self.link_repo.get_all()
    cache: dict[str, Resolution] = {}

    def resolve(text: str) -> Resolution:
      key = task_key(text)
      if key not in cache:
        cache[key] = resolve_key(key, links, goals)
      return cache[key]

    return resolve

  # ---- decisions

  def set_link(self, text_or_key: str, kind: str, goal_id: Optional[int]) -> str:
    """Save a decision and return the key it applies to. Raises ValueError (bad input) or LookupError (no goal)."""
    key = task_key(text_or_key)
    if not key:
      raise ValueError("A task needs some text to link")
    link = TaskLinkWrite(key=key, kind=kind, goal_id=goal_id)  # type: ignore[arg-type]
    if link.goal_id is not None and self.goal_repo.get_by_id(link.goal_id) is None:
      raise LookupError("Goal not found")
    self.link_repo.upsert(link)
    return key

  def clear_link(self, text_or_key: str) -> bool:
    return self.link_repo.delete(task_key(text_or_key))

  # ---- review queue

  def review_queue(self, limit: int = 50) -> dict:
    """Completed tasks whose goal is unknown, most-repeated first. Only completed tasks matter: alignment
    counts nothing else."""
    resolve = self.resolver()
    seen: dict[str, dict] = {}
    for log in self.log_repo.get_all():
      for task in planned_task_list(log):
        text = str(task["text"]).strip()
        key = task_key(text)
        entry = seen.setdefault(key, {"key": key, "text": text, "done": 0, "planned": 0, "last_date": log.date})
        entry["planned"] += 1
        entry["done"] += 1 if task.get("completed") else 0
        if log.date >= entry["last_date"]:
          entry["last_date"] = log.date
          entry["text"] = text
    queue = [e for e in seen.values() if e["done"] > 0 and resolve(e["text"]).kind == "unreviewed"]
    queue.sort(key=lambda e: (-e["done"], -e["planned"], e["key"]))
    return {
      "unreviewed_completed_keys": len(queue),
      "items": [{**e, "last_date": e["last_date"].isoformat()} for e in queue[:limit]],
    }

  # ---- attention per goal

  def goal_attention(self, days: int = 14, as_of: Optional[date] = None) -> list[dict]:
    """Per active goal: completed tasks in the last `days` and 30 days, the last day one was done, and the
    quiet stretch since. Measured from the last logged day (not today): the journal is imported in batches."""
    logs = self.log_repo.get_all()
    if not logs:
      return []
    as_of = as_of or max(log.date for log in logs)
    goals = self.goal_repo.get_active()
    resolve = self.resolver(goals)
    done: dict[int, list[date]] = {goal.id: [] for goal in goals}
    for log in logs:
      if log.date > as_of:
        continue
      for text in completed_texts(log):
        resolution = resolve(text)
        if resolution.kind == "goal" and resolution.goal_id in done:
          done[resolution.goal_id].append(log.date)
    result = []
    for goal in goals:
      dates = done[goal.id]
      last = max(dates) if dates else None
      result.append(
        {
          "goal_id": goal.id,
          "title": goal.title.strip(),
          "horizon": goal.horizon,
          "done_recent": sum(1 for d in dates if d > as_of - timedelta(days=days)),
          "done_30d": sum(1 for d in dates if d > as_of - timedelta(days=30)),
          "last_done_date": last.isoformat() if last else None,
          "days_quiet": (as_of - last).days if last else None,
          "window_days": days,
          "as_of": as_of.isoformat(),
        }
      )
    return result
