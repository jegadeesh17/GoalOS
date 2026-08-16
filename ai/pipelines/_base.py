"""Shared pipeline utilities."""

import json
from pathlib import Path
from typing import Any

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(name: str) -> str:
  return (PROMPTS_DIR / f"{name}.txt").read_text(encoding="utf-8")


def format_context(context: dict[str, Any]) -> str:
  return json.dumps(context, indent=2, default=str)


def fallback_morning(context: dict) -> dict:
  from services.mentor_briefing import personalized_fallback_rule
  briefing = context.get("mentor_briefing")
  if briefing:
    return personalized_fallback_rule(briefing)
  return {
    "mentor_rule": "You will complete your #1 task before opening your phone. No exceptions.",
    "why_this_rule": "Set your OpenRouter API key in Settings for fully personalized mentoring.",
    "past_mistake_called_out": "No journal history loaded yet.",
    "goal_connection": "Define your 1-, 5-, and 10-year goals on the Goals page.",
    "if_you_ignore_this": "Another generic day instead of targeted growth.",
    "confidence": 0.2,
    "source": "generic_fallback",
  }


def fallback_evening(context: dict) -> dict:
  from services.pattern_service import PatternService
  recent_logs = context.get("recent_logs", [])
  pattern_report = PatternService().analyze_patterns(recent_logs)
  primary_loop = pattern_report.get("primary_unhealthy_loop")
  isolated = pattern_report.get("isolated_friction_events", [])

  if primary_loop:
    pattern_text = f"Repeating pattern: {primary_loop['pattern_name']} ({primary_loop['occurrences_count']}x observed)"
    actionable_break = primary_loop["actionable_countermeasure"]
  elif isolated:
    pattern_text = f"Isolated event on {isolated[0]['date_observed']} ({isolated[0]['event_name']}) — not a chronic loop"
    actionable_break = "Reset cleanly tomorrow morning without deviating from your core plan."
  else:
    pattern_text = "Consistent execution across recent logs"
    actionable_break = "Protect your morning deep work block to keep momentum compounding."

  return {
    "journal_insights": ["Consistent reflection builds high self-awareness and accountability."],
    "scores": {
      "goal_alignment_score": 50.0,
      "consistency_score": 50.0,
      "health_score": 50.0,
      "learning_score": 50.0,
      "productivity_score": 50.0,
    },
    "one_thing_done_well": "You showed up and logged today's honest review",
    "one_improvement": "Focus on the first 90 minutes of the morning",
    "tomorrow_first_task": "Execute your #1 priority task first",
    "pattern_detected": pattern_text,
    "actionable_pattern_break": actionable_break,
    "commitment_extracted": None,
    "memories_to_store": [],
    "confidence": 0.5,
    "source": "deterministic_fallback",
  }


def fallback_weekly(context: dict) -> dict:
  from services.pattern_service import PatternService
  stats = context.get("week_task_stats", {})
  rate = stats.get("week_completion_rate")
  rate_text = f"{rate}%" if rate is not None else "unknown"
  weeks_left = context.get("weeks_remaining_in_month", 3)
  week_logs = context.get("week_logs", []) or context.get("recent_logs", [])
  
  pattern_report = PatternService().analyze_patterns(week_logs)
  primary_loop = pattern_report.get("primary_unhealthy_loop")
  recurring = [p["pattern_name"] for p in pattern_report.get("repeating_unhealthy_patterns", [])]

  if primary_loop:
    primary_pat = f"{primary_loop['pattern_name']} ({primary_loop['occurrences_count']}x observed)"
    pattern_break = primary_loop["actionable_countermeasure"]
    mentor_rule = f"Eliminate {primary_loop['pattern_name']}: {primary_loop['actionable_countermeasure']}"
  else:
    primary_pat = "Task deferral past noon"
    pattern_break = "Lock in your core deep work block within 90 minutes of waking."
    mentor_rule = "Complete your core deep work task in the first 2 hours of the morning. No exceptions."

  return {
    "week_summary": "Weekly execution logged. Multi-day patterns determine whether you hit monthly milestones.",
    "task_stats_commentary": f"Task completion rate: {rate_text}. Single-day dips are manageable, but chronic patterns must be eliminated.",
    "urgent_takeaway": f"You have {weeks_left} weeks remaining in the month. Dismantle repeating friction loops now.",
    "one_month_progress": "Pacing depends directly on eliminating recurring anti-patterns.",
    "cascading_year_impact": "Consistently overcoming behavioral friction loops safeguards 1-Year and 5-Year horizons.",
    "wins": ["Maintained consistent daily journaling and progress tracking"],
    "failures": ["Delayed deep work start", "Allowed secondary distractions into focus windows"],
    "recurring_mistakes": recurring or ["Postponing hard tasks past noon", "Distraction during focus blocks"],
    "primary_unhealthy_pattern": primary_pat,
    "actionable_pattern_break": pattern_break,
    "weekly_score": 65.0,
    "mentor_rule_for_next_week": mentor_rule,
    "one_percent_focus": "Protect your morning deep work block from all digital interruptions.",
    "confidence": 0.6,
    "source": "deterministic_fallback",
  }


def fallback_goal_alignment(context: dict) -> dict:
  goals = context.get("active_goals", [])
  titles = [g.get("title", g.title if hasattr(g, "title") else "") for g in goals[:3]]
  return {
    "alignment_narrative": "Review your goal alignment regularly.",
    "aligned_goals": titles[:1],
    "neglected_goals": titles[1:],
    "recommendation": "Pick one neglected goal to focus on this week.",
    "confidence": 0.3,
  }


def fallback_reflection(context: dict) -> dict:
  return {
    "insights": ["Reflection is valuable"],
    "commitments": [],
    "patterns": [],
    "memories_to_store": [],
    "confidence": 0.3,
  }


def fallback_future_self(context: dict) -> dict:
  return {
    "message": "I know this period feels challenging. The struggles you're facing now are shaping who you'll become. Keep showing up.",
    "written_from_age": 35,
    "key_things_referenced": ["consistency", "growth"],
    "confidence": 0.3,
  }


def fallback_progress(context: dict) -> dict:
  from services.pattern_service import PatternService
  goals = context.get("active_goals", [])
  short_term = [g.get("title", "") for g in goals if (g.get("horizon") or "").lower().strip() in ("1-month", "1_month", "short", "monthly")]
  primary_goal = short_term[0] if short_term else (goals[0].get("title", "") if goals else "Establish daily deep work discipline")
  progress = context.get("monthly_progress", {})
  days_logged = progress.get("days_logged", 0)
  days_in_month = progress.get("days_in_month", 31)
  month_name = context.get("month_name") or progress.get("month_name") or "Current Month"
  
  recent_logs = context.get("recent_logs", [])
  pattern_report = PatternService().analyze_patterns(recent_logs, goals)
  primary_loop = pattern_report.get("primary_unhealthy_loop")
  isolated = pattern_report.get("isolated_friction_events", [])

  if primary_loop:
    p_name = primary_loop["pattern_name"]
    p_count = primary_loop["occurrences_count"]
    p_dates = ", ".join(primary_loop["dates_observed"][:3])
    bottleneck = f"Repeating anti-pattern: {p_name} ({p_count}x recorded on {p_dates})."
    pattern_analysis = (
      f"🚨 **Chronic Loop Identified:** {p_name} was recorded {p_count} times ({p_dates}). "
      f"A single bad day is normal noise, but this repeating pattern is the primary bottleneck pulling down your 1-Month goal trajectory."
    )
    pattern_protocol = primary_loop["actionable_countermeasure"]
    advice = f"Break this loop immediately: {primary_loop['actionable_countermeasure']}"
  elif isolated:
    bottleneck = f"Isolated friction on {isolated[0]['date_observed']} ({isolated[0]['event_name']})."
    pattern_analysis = f"ℹ️ Recent friction on {isolated[0]['date_observed']} was an isolated event, not a chronic loop. Do not overreact; maintain baseline discipline."
    pattern_protocol = "Execute standard morning routine without unnecessary changes."
    advice = f"Maintain momentum and execute your top morning deep work block for: '{primary_goal}'."
  else:
    bottleneck = "Inconsistent morning startup time."
    pattern_analysis = "✅ No chronic friction loops detected in recent history. Execution is consistent."
    pattern_protocol = "Protect the first 90 minutes of the morning for deep work."
    advice = f"Lock in your top 90-minute morning deep work block specifically targeted at: '{primary_goal}'."

  if days_logged > 0:
    narrative = f"You logged {days_logged}/{days_in_month} days in {month_name}. Execution trajectory is evaluating pacing toward '{primary_goal}'."
    wins = progress.get("wins") or "Journal logs recorded."
    pacing = progress.get("pacing_status", "On Track")
  else:
    narrative = f"Current Month Tracking ({month_name}): 0 of {days_in_month} days logged so far. Evaluate Day 1 pacing toward '{primary_goal}'."
    hist_logs = context.get("historical_baseline_logs", [])
    if hist_logs:
      past_wins = [l.get("takeaway") or l.get("journal_entry") for l in hist_logs if l.get("takeaway") or l.get("journal_entry")]
      wins = f"No entries for {month_name} yet. Baseline momentum from previous month:\n" + "\n".join(f"• {w[:80]}..." for w in past_wins[:3])
    else:
      wins = f"No journal entries logged yet for {month_name}."
    pacing = "Day 1 Pacing — Start Daily Log"

  return {
    "pacing_status": pacing,
    "monthly_goal_evaluated": primary_goal,
    "progress_narrative": narrative,
    "key_wins_aligned": wins,
    "critical_bottleneck": bottleneck,
    "recognized_pattern_analysis": pattern_analysis,
    "actionable_pattern_breaking_protocol": pattern_protocol,
    "actionable_coaching_advice": advice,
    "source": "heuristic_fallback",
    "confidence": 0.6,
  }
