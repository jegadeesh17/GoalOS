"""Behavioral Pattern Recognition Engine for GoalOS.

Distinguishes isolated 1-day friction (noise) from repeating unhealthy patterns (signal),
and synthesizes actionable pattern-breaking protocols to protect 1-Month and 1-Year goals.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import Any, Optional


DISTRACTION_KEYWORDS = {
  "phone": ["phone", "scrolling", "instagram", "reels", "shorts", "twitter", "x.com", "reddit"],
  "entertainment": ["youtube", "video", "netflix", "movies", "anime", "gaming", "stream"],
  "procrastination": ["procrastinated", "procrastination", "wasted time", "waste time", "drifted", "drifting", "slacking", "lazy", "postponed", "delayed", "put off"],
  "porn_dopamine": ["porn", "masturbat", "relapse", "cheap dopamine", "lust", "dopamine trap"],
  "focus_shatter": ["multitasking", "overthinking", "lost focus", "no focus", "distracted", "scattered", "brain fog"],
  "fatigue_slump": ["fatigue", "exhausted", "tired", "sleepy", "afternoon slump", "no energy", "low energy", "drained"],
}


class PatternService:
  """Analyzes multi-day journal history to isolate repeating behavioral loops."""

  @staticmethod
  def _to_dict(obj: Any) -> dict:
    if obj is None:
      return {}
    if hasattr(obj, "model_dump"):
      return obj.model_dump(mode="json")
    if isinstance(obj, dict):
      return obj
    return {}

  @staticmethod
  def _parse_tasks(log_dict: dict) -> list[dict]:
    raw = log_dict.get("planned_tasks")
    if not raw:
      return []
    if isinstance(raw, list):
      return raw
    if isinstance(raw, str):
      try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else []
      except (json.JSONDecodeError, TypeError):
        pass
    return []

  def analyze_patterns(
    self,
    recent_logs: list[Any],
    active_goals: list[Any] | None = None,
    memories: list[Any] | None = None,
    target_date: date | None = None,
  ) -> dict[str, Any]:
    """Perform comprehensive multi-day pattern recognition across journal logs."""
    target_date = target_date or date.today()
    logs = [self._to_dict(l) for l in recent_logs if l]
    logs.sort(key=lambda x: str(x.get("date", "")), reverse=True)

    # 1. Distraction and Behavioral Friction Tracking across dates
    keyword_occurrences: dict[str, list[dict[str, str]]] = defaultdict(list)
    review_takeaways: list[dict[str, str]] = []
    daily_stats: list[dict[str, Any]] = []
    incomplete_tasks_by_name: dict[str, list[str]] = defaultdict(list)

    for l in logs:
      log_date = str(l.get("date", ""))
      review = (l.get("journal_entry") or "").strip()
      takeaway = (l.get("takeaway") or l.get("one_lesson") or "").strip()
      gratitude = (l.get("gratitude") or "").strip()
      combined_text = f"{review} {takeaway} {gratitude}".lower()

      if review or takeaway:
        review_takeaways.append({
          "date": log_date,
          "review": review,
          "takeaway": takeaway,
        })

      # Scan for friction keyword categories
      for category, kws in DISTRACTION_KEYWORDS.items():
        matched = [kw for kw in kws if kw in combined_text]
        if matched:
          snippet = review if review else takeaway
          keyword_occurrences[category].append({
            "date": log_date,
            "matched_keywords": ", ".join(matched),
            "snippet": snippet[:180],
          })

      # Tasks analysis
      tasks = self._parse_tasks(l)
      completed_count = sum(1 for t in tasks if t.get("completed"))
      total_count = len(tasks)
      completion_rate = float(l.get("task_completion_rate")) if l.get("task_completion_rate") is not None else (
        (completed_count / total_count * 100) if total_count > 0 else None
      )

      for t in tasks:
        t_text = (t.get("text") or "").strip()
        if t_text and not t.get("completed"):
          normalized_title = " ".join(re.findall(r"[a-zA-Z0-9]+", t_text.lower()))
          if len(normalized_title) >= 4:
            incomplete_tasks_by_name[normalized_title].append(log_date)

      daily_stats.append({
        "date": log_date,
        "completion_rate": completion_rate,
        "tasks_planned": total_count,
        "tasks_completed": completed_count,
        "sleep_hours": l.get("sleep_hours"),
        "mood": l.get("mood_morning"),
        "deep_work_hours": l.get("deep_work_hours"),
      })

    # 2. Categorize Patterns: Chronic (Repeating >= 2) vs Acute (1-Day isolated)
    repeating_unhealthy_patterns: list[dict[str, Any]] = []
    isolated_friction_events: list[dict[str, Any]] = []

    # A. Distraction & Behavioral categories
    category_meta = {
      "phone": {
        "name": "Morning Phone & Feed Scrolling Loop",
        "trigger": "Reaching for phone before completing the top priority deep work task.",
        "protocol": "Implement strict Phone-in-Another-Room rule until #1 priority task is 100% done.",
      },
      "entertainment": {
        "name": "Entertainment / Video Binging Dopamine Leak",
        "trigger": "Using YouTube/streams as a relief valve during cognitive friction.",
        "protocol": "Use URL blocklist or isolate deep work station from browser entertainment.",
      },
      "procrastination": {
        "name": "Task Avoidance & Execution Delay",
        "trigger": "Over-planning or waiting for 'perfect mood' rather than starting with a 10-minute micro-step.",
        "protocol": "Use the 5-minute activation rule: open the file and write 1 paragraph or 5 lines of code immediately.",
      },
      "porn_dopamine": {
        "name": "Compulsive Dopamine Seeking Trap",
        "trigger": "Unmanaged stress, boredom, or late-night fatigue leading to immediate gratification.",
        "protocol": "Hard shutdown of screens 60 mins before bed and immediate physical reset (walk/pushups) when urge triggers.",
      },
      "focus_shatter": {
        "name": "Multitasking & Cognitive Fragmentation",
        "trigger": "Switching between multiple tabs/tasks without closing loops.",
        "protocol": "Enforce single-task work blocks: only 1 window open per 45-minute focus sprint.",
      },
      "fatigue_slump": {
        "name": "Afternoon Energy Crash & Slump",
        "trigger": "Sub-optimal sleep (<6.5h) or heavy carb lunch during midday transition.",
        "protocol": "Schedule a 15-minute screen-free walk or light rest instead of passive scrolling during energy dips.",
      },
    }

    for cat, occurrences in keyword_occurrences.items():
      count = len(occurrences)
      meta = category_meta.get(cat, {
        "name": f"Recurring {cat.replace('_', ' ').title()}",
        "trigger": "Repeated friction across daily logs.",
        "protocol": "Set an explicit non-negotiable rule to eliminate the trigger.",
      })
      dates = [o["date"] for o in occurrences]
      snippets = [o["snippet"] for o in occurrences if o.get("snippet")]

      if count >= 2:
        severity = "critical" if count >= 3 else "warning"
        repeating_unhealthy_patterns.append({
          "category": cat,
          "pattern_name": meta["name"],
          "occurrences_count": count,
          "dates_observed": dates[:5],
          "severity": severity,
          "root_trigger": meta["trigger"],
          "actionable_countermeasure": meta["protocol"],
          "evidence_quotes": snippets[:3],
          "impact_verdict": f"Observed {count}x across {', '.join(dates[:3])}. This repeating pattern systematically erodes daily goal pacing.",
        })
      elif count == 1:
        isolated_friction_events.append({
          "category": cat,
          "event_name": meta["name"],
          "date_observed": dates[0],
          "evidence": snippets[0] if snippets else "",
          "reset_advice": "Isolated 1-day event. Reset cleanly tomorrow without changing core strategy.",
        })

    # B. Repeatedly Incomplete Tasks (Planning vs Execution gap)
    for task_name, dates in incomplete_tasks_by_name.items():
      if len(dates) >= 2:
        repeating_unhealthy_patterns.append({
          "category": "task_rollover",
          "pattern_name": f'Repeated Task Deferral: "{task_name.capitalize()}"',
          "occurrences_count": len(dates),
          "dates_observed": dates[:5],
          "severity": "critical" if len(dates) >= 3 else "warning",
          "root_trigger": "Task is either scoped too ambiguously or continuously postponed for low-friction busywork.",
          "actionable_countermeasure": f'Break down "{task_name}" into an actionable 15-minute sub-task and schedule it as Task #1 tomorrow morning.',
          "evidence_quotes": [f'Postponed on: {", ".join(dates[:4])}'],
          "impact_verdict": f'Planned and left unfinished {len(dates)} times. Chronic rollover destroys execution trust.',
        })

    # C. Planning Fallacy (Overplanning with low execution)
    overplanned_days = [
      d for d in daily_stats
      if d.get("tasks_planned", 0) >= 5 and (d.get("completion_rate") is not None and d.get("completion_rate") < 50)
    ]
    if len(overplanned_days) >= 2:
      op_dates = [d["date"] for d in overplanned_days]
      repeating_unhealthy_patterns.append({
        "category": "planning_fallacy",
        "pattern_name": "Overplanning Fallacy (High Task Count, Low Follow-through)",
        "occurrences_count": len(overplanned_days),
        "dates_observed": op_dates[:4],
        "severity": "warning",
        "root_trigger": "Putting too many secondary tasks on the list instead of committing to 1-2 essential milestones.",
        "actionable_countermeasure": "Cap tomorrow's daily plan at maximum 3 priority tasks. The first must be 100% complete before task 2 begins.",
        "evidence_quotes": [f"Planned 5+ tasks with <50% completion on: {', '.join(op_dates[:3])}"],
        "impact_verdict": f"Occurred on {len(overplanned_days)} days. Quality of execution beats quantity of uncompleted tasks.",
      })

    # D. Sleep-Execution Correlation
    sleep_deprived_days = [
      d for d in daily_stats
      if d.get("sleep_hours") is not None and d.get("sleep_hours") < 6.0
    ]
    if len(sleep_deprived_days) >= 2:
      sd_dates = [d["date"] for d in sleep_deprived_days]
      repeating_unhealthy_patterns.append({
        "category": "sleep_deficit",
        "pattern_name": "Sleep Deficit Dragging Morning Performance",
        "occurrences_count": len(sleep_deprived_days),
        "dates_observed": sd_dates[:4],
        "severity": "warning",
        "root_trigger": "Late-night screen usage or irregular sleep schedule reducing cognitive stamina.",
        "actionable_countermeasure": "Set a non-negotiable bedtime boundary. 7+ hours of sleep is the prerequisite for deep work execution.",
        "evidence_quotes": [f"Sleep < 6.0h recorded on: {', '.join(sd_dates[:3])}"],
        "impact_verdict": f"Sleep deficit observed on {len(sleep_deprived_days)} days. Cognitive fatigue is the root catalyst of distraction.",
      })

    # E. Compounding Winning Patterns
    high_perf_days = [
      d for d in daily_stats
      if d.get("completion_rate") is not None and d.get("completion_rate") >= 75.0
    ]
    compounding_healthy_patterns: list[dict[str, Any]] = []
    if len(high_perf_days) >= 2:
      hp_dates = [d["date"] for d in high_perf_days]
      compounding_healthy_patterns.append({
        "pattern_name": "High-Execution Momentum Days",
        "occurrences_count": len(high_perf_days),
        "dates_observed": hp_dates[:4],
        "evidence": f"Achieved >=75% task completion on: {', '.join(hp_dates[:4])}",
        "reinforcement_rule": "Replicate the exact morning routine from your high-execution days (early start + locked focus block).",
      })

    # 3. Sort repeating patterns by severity (critical first) and occurrences count
    repeating_unhealthy_patterns.sort(
      key=lambda p: (0 if p.get("severity") == "critical" else 1, -p.get("occurrences_count", 0))
    )

    primary_loop = repeating_unhealthy_patterns[0] if repeating_unhealthy_patterns else None

    # 4. Construct high-clarity summary narrative
    if primary_loop:
      summary = (
        f"🚨 **Primary Unhealthy Pattern Detected:** {primary_loop['pattern_name']} "
        f"({primary_loop['occurrences_count']}x recorded across {', '.join(primary_loop['dates_observed'][:3])}). "
        f"**Why this matters more than 1-day friction:** Isolated bad days are normal, but this repeating loop is actively "
        f"undermining your 1-Month and 1-Year goals. Immediate action: {primary_loop['actionable_countermeasure']}"
      )
    elif isolated_friction_events:
      summary = (
        f"ℹ️ **No Chronic Patterns Detected:** Recent friction on {isolated_friction_events[0]['date_observed']} "
        f"was an isolated event ({isolated_friction_events[0]['event_name']}). Do not overreact—maintain standard daily execution."
      )
    else:
      summary = "✅ **Consistent Execution:** No major repeating friction patterns detected in recent journal history. Keep momentum compounding."

    return {
      "target_date": target_date.isoformat(),
      "total_logs_analyzed": len(logs),
      "repeating_unhealthy_patterns": repeating_unhealthy_patterns,
      "isolated_friction_events": isolated_friction_events,
      "compounding_healthy_patterns": compounding_healthy_patterns,
      "primary_unhealthy_loop": primary_loop,
      "summary_narrative": summary,
      "has_chronic_patterns": len(repeating_unhealthy_patterns) > 0,
    }
