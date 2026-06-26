"""Build a personalized mentor briefing from real journal data — not generic coaching."""

import json
import re
from collections import Counter
from datetime import date

from models.daily_log import DailyLog


def _clip(text: str | None, max_len: int = 220) -> str:
  if not text:
    return ""
  text = " ".join(text.split())
  return text if len(text) <= max_len else text[: max_len - 3] + "..."


def _tasks_from_log_dict(log: dict) -> list[dict]:
  if log.get("planned_tasks"):
    try:
      return json.loads(log["planned_tasks"]) if isinstance(log["planned_tasks"], str) else log["planned_tasks"]
    except (json.JSONDecodeError, TypeError):
      pass
  return []


def _today_tasks(today_log: dict | None) -> list[dict]:
  if not today_log:
    return []
  raw = today_log.get("planned_tasks")
  if not raw:
    return []
  try:
    tasks = json.loads(raw) if isinstance(raw, str) else raw
    if isinstance(tasks, list):
      return sorted(tasks, key=lambda t: t.get("priority", 99))
  except (json.JSONDecodeError, TypeError):
    pass
  return []


def build_mentor_briefing(
  target_date: date,
  today_log: DailyLog | dict | None,
  recent_logs: list[DailyLog | dict],
  user_vision: dict | None = None,
  recent_coach_advice: list | None = None,
) -> dict:
  """Extract specifics from journals for mentor AI or personalized fallback."""
  if isinstance(today_log, DailyLog):
    today_log = today_log.model_dump(mode="json")

  log_dicts = [
    l.model_dump(mode="json") if isinstance(l, DailyLog) else l
    for l in recent_logs
    if l
  ]

  # Today's priority tasks
  today_tasks = _today_tasks(today_log)

  # Past journal quotes
  reviews: list[dict] = []
  takeaways: list[dict] = []
  completion_rates: list[float] = []
  incomplete_tasks: list[str] = []
  sleep_mood: list[dict] = []

  for log in log_dicts:
    log_date = log.get("date", "")
    if log_date == target_date.isoformat():
      continue

    review = (log.get("journal_entry") or "").strip()
    takeaway = (log.get("takeaway") or log.get("one_lesson") or "").strip()
    if review:
      reviews.append({"date": log_date, "text": _clip(review, 300)})
    if takeaway:
      takeaways.append({"date": log_date, "text": _clip(takeaway, 160)})

    rate = log.get("task_completion_rate")
    if rate is not None:
      completion_rates.append(float(rate))

    for t in _tasks_from_log_dict(log):
      text = (t.get("text") or "").strip()
      if text and not t.get("completed"):
        incomplete_tasks.append(text.lower())

    if log.get("sleep_hours") is not None or log.get("mood_morning") is not None:
      sleep_mood.append({
        "date": log_date,
        "sleep_hours": log.get("sleep_hours"),
        "mood": log.get("mood_morning"),
      })

  # Recurring incomplete tasks
  task_counts = Counter(incomplete_tasks)
  repeated_failures = [
    {"task": text, "times_incomplete": count}
    for text, count in task_counts.most_common(5)
    if count >= 2
  ]

  # Recurring words in reviews (mistake language)
  review_words: list[str] = []
  stop = {
    "the", "and", "for", "that", "with", "this", "from", "have", "were", "was",
    "not", "but", "your", "you", "are", "had", "did", "very", "just", "today",
  }
  for r in reviews[:10]:
    review_words.extend(
      w.lower() for w in re.findall(r"[a-zA-Z]{5,}", r["text"]) if w.lower() not in stop
    )
  recurring_themes = [w for w, _ in Counter(review_words).most_common(6)]

  # Last mentor rules (avoid repetition)
  prior_rules: list[str] = []
  if recent_coach_advice:
    for advice in recent_coach_advice[:4]:
      try:
        payload = json.loads(advice.get("ai_response", "{}"))
        if payload.get("mentor_rule"):
          prior_rules.append(payload["mentor_rule"])
      except (json.JSONDecodeError, TypeError):
        pass

  avg_completion = (
    round(sum(completion_rates) / len(completion_rates), 1) if completion_rates else None
  )

  visions = user_vision or {}
  top_task = today_tasks[0]["text"] if today_tasks else None

  return {
    "date": target_date.isoformat(),
    "one_year_goal": visions.get("one_year_vision") or "",
    "five_year_goal": visions.get("five_year_vision") or "",
    "ten_year_goal": visions.get("ten_year_vision") or "",
    "todays_priority_tasks": [t["text"] for t in today_tasks[:6]],
    "top_priority_task": top_task,
    "recent_reviews": reviews[:5],
    "recent_takeaways": takeaways[:5],
    "most_recent_review": reviews[0] if reviews else None,
    "most_recent_takeaway": takeaways[0]["text"] if takeaways else "",
    "avg_task_completion_7d": avg_completion,
    "repeated_incomplete_tasks": repeated_failures,
    "recurring_review_themes": recurring_themes,
    "recent_sleep_mood": sleep_mood[:5],
    "prior_mentor_rules": prior_rules,
    "days_of_history": len(log_dicts),
  }


def format_briefing_for_prompt(briefing: dict) -> str:
  """Human-readable briefing block for the LLM."""
  lines = [
    "=== PERSONALIZED MENTOR BRIEFING (use these specifics — do NOT be generic) ===",
    f"Date: {briefing.get('date')}",
    "",
  ]

  if briefing.get("one_year_goal"):
    lines += [
      "LONG-TERM GOALS (priority 1yr > 5yr > 10yr):",
      f"  1-year: {briefing['one_year_goal']}",
      f"  5-year: {briefing.get('five_year_goal') or '(not set)'}",
      f"  10-year: {briefing.get('ten_year_goal') or '(not set)'}",
      "",
    ]

  tasks = briefing.get("todays_priority_tasks") or []
  if tasks:
    lines.append("TODAY'S TASKS (priority order, #1 first):")
    for i, t in enumerate(tasks, 1):
      lines.append(f"  #{i}: {t}")
    lines.append("")

  if briefing.get("most_recent_review"):
    r = briefing["most_recent_review"]
    lines.append(f"MOST RECENT REVIEW ({r['date']}):")
    lines.append(f'  "{r["text"]}"')
    lines.append("")

  for r in briefing.get("recent_reviews", [])[1:3]:
    lines.append(f"REVIEW ({r['date']}): \"{r['text']}\"")
  if briefing.get("recent_reviews"):
    lines.append("")

  for t in briefing.get("recent_takeaways", [])[:3]:
    lines.append(f"TAKEAWAY ({t['date']}): \"{t['text']}\"")
  if briefing.get("recent_takeaways"):
    lines.append("")

  if briefing.get("repeated_incomplete_tasks"):
    lines.append("TASKS YOU KEEP PLANNING BUT NOT FINISHING:")
    for item in briefing["repeated_incomplete_tasks"]:
      lines.append(f"  - \"{item['task']}\" (incomplete {item['times_incomplete']}x in recent logs)")
    lines.append("")

  if briefing.get("avg_task_completion_7d") is not None:
    lines.append(f"AVG TASK COMPLETION (recent): {briefing['avg_task_completion_7d']}%")
    lines.append("")

  if briefing.get("recurring_review_themes"):
    lines.append(f"WORDS YOU USE IN REVIEWS OFTEN: {', '.join(briefing['recurring_review_themes'])}")
    lines.append("")

  if briefing.get("prior_mentor_rules"):
    lines.append("DO NOT REPEAT THESE PRIOR RULES:")
    for rule in briefing["prior_mentor_rules"]:
      lines.append(f"  - {rule}")
    lines.append("")

  lines.append(
    "INSTRUCTION: Quote or reference at least ONE specific review, takeaway, or failed task above. "
    "Tie today's rule to their #1 task and 1-year goal."
  )
  return "\n".join(lines)


def personalized_fallback_rule(briefing: dict) -> dict:
  """Data-driven rule when LLM is unavailable — still uses their journal."""
  top_task = briefing.get("top_priority_task") or "your #1 task today"
  review = briefing.get("most_recent_review")
  takeaway = briefing.get("most_recent_takeaway") or ""
  repeated = briefing.get("repeated_incomplete_tasks") or []
  one_year = briefing.get("one_year_goal") or "your 1-year goal"
  avg = briefing.get("avg_task_completion_7d")

  if repeated:
    failed = repeated[0]["task"]
    mistake = f'You planned "{failed}" multiple times and did not finish it.'
    rule = f'You will complete "{top_task}" before touching your phone or YouTube. No exceptions.'
    why = f"{mistake} Your reviews show the same loop."
  elif review:
    mistake = _clip(review["text"], 120)
    rule = f'You will start with "{top_task}" in the first 90 minutes after waking. No phone until it is done.'
    why = f'On {review["date"]} you wrote: "{mistake}"'
  elif takeaway:
    rule = f'You will act on your own takeaway: {takeaway}'
    why = "You already know what to fix — today you prove it with action, not more planning."
    mistake = "Writing takeaways you don't follow."
  else:
    rule = f'You will complete "{top_task}" before any entertainment. No exceptions.'
    why = "No more planning without execution."
    mistake = "Plans without follow-through."

  consequence = f"Your 1-year goal ({_clip(one_year, 80)}) slips another day."
  if avg is not None and avg < 50:
    consequence = f"At {avg}% task completion, you are not serious yet. {consequence}"

  return {
    "mentor_rule": rule,
    "why_this_rule": why,
    "past_mistake_called_out": mistake,
    "goal_connection": f"This directly serves: {_clip(one_year, 100)}",
    "if_you_ignore_this": consequence,
    "confidence": 0.5,
    "source": "personalized_fallback",
  }
