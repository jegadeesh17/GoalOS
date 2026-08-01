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
  return {
    "journal_insights": ["Reflection helps you improve"],
    "scores": {
      "goal_alignment_score": 50.0,
      "consistency_score": 50.0,
      "health_score": 50.0,
      "learning_score": 50.0,
      "productivity_score": 50.0,
    },
    "one_thing_done_well": "You showed up and reflected",
    "one_improvement": "Focus on your top priority tomorrow",
    "tomorrow_first_task": "Review your morning plan",
    "pattern_detected": "Unable to detect patterns without AI",
    "commitment_extracted": None,
    "memories_to_store": [],
    "confidence": 0.3,
  }


def fallback_weekly(context: dict) -> dict:
  stats = context.get("week_task_stats", {})
  rate = stats.get("week_completion_rate")
  rate_text = f"{rate}%" if rate is not None else "unknown"
  weeks_left = context.get("weeks_remaining_in_month", 3)
  
  return {
    "week_summary": "You logged days this week but deep work execution needs aggressive focus.",
    "task_stats_commentary": f"Task completion rate: {rate_text}. You must finish high-ROI deep work first thing in the morning.",
    "urgent_takeaway": f"You have {weeks_left} weeks remaining in the month. Lock in uninterrupted deep work blocks every morning to meet your 1-Month goal.",
    "one_month_progress": "Progress pacing is moderate. Ensure daily tasks directly map to your 1-Month goal.",
    "cascading_year_impact": "Consistently completing 1-Month goals safeguards your 1-Year milestone and 5-Year vision.",
    "wins": ["Maintained consistent journaling discipline"],
    "failures": ["Deep work delayed by secondary tasks", "Incomplete priority execution"],
    "recurring_mistakes": ["Postponing hard tasks past noon", "Distraction during focus blocks"],
    "weekly_score": 60.0,
    "mentor_rule_for_next_week": "Complete your core deep work task in the first 2 hours of the morning. No exceptions.",
    "one_percent_focus": "Protect your morning deep work block from all interruptions.",
    "confidence": 0.5,
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
  goals = context.get("active_goals", [])
  short_term = [g.get("title", "") for g in goals if (g.get("horizon") or "").lower().strip() in ("1-month", "1_month", "short", "monthly")]
  primary_goal = short_term[0] if short_term else (goals[0].get("title", "") if goals else "Establish daily deep work discipline")
  progress = context.get("monthly_progress", {})
  days_logged = progress.get("days_logged", 0)
  days_in_month = progress.get("days_in_month", 31)
  month_name = context.get("month_name") or progress.get("month_name") or "Current Month"

  if days_logged > 0:
    narrative = f"You logged {days_logged}/{days_in_month} days in {month_name}. Execution is directly moving you toward '{primary_goal}'."
    wins = progress.get("wins") or "Journal logs recorded."
    pacing = progress.get("pacing_status", "On Track")
    bottleneck = "Multitasking or delaying morning focus blocks."
    advice = f"Lock in your top 90-minute morning deep work block specifically targeted at: '{primary_goal}'."
  else:
    narrative = f"Current Month Tracking ({month_name}): 0 of {days_in_month} days logged so far. Evaluate Day 1 pacing toward '{primary_goal}'."
    hist_logs = context.get("historical_baseline_logs", [])
    if hist_logs:
      past_wins = [l.get("takeaway") or l.get("journal_entry") for l in hist_logs if l.get("takeaway") or l.get("journal_entry")]
      wins = f"No entries for {month_name} yet. Baseline momentum from previous month:\n" + "\n".join(f"• {w[:80]}..." for w in past_wins[:3])
    else:
      wins = f"No journal entries logged yet for {month_name}."
    pacing = "Day 1 Pacing — Start Daily Log"
    bottleneck = f"No daily logs recorded yet for {month_name}."
    advice = f"Upload your daily handwritten journal pages or complete a digital entry to start pacing toward '{primary_goal}'."

  return {
    "pacing_status": pacing,
    "monthly_goal_evaluated": primary_goal,
    "progress_narrative": narrative,
    "key_wins_aligned": wins,
    "critical_bottleneck": bottleneck,
    "actionable_coaching_advice": advice,
    "source": "heuristic_fallback",
    "confidence": 0.5,
  }
