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
    "goal_connection": "Define your 1-year goal on the Goals page.",
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
  return {
    "week_summary": "You logged days but execution needs work.",
    "task_stats_commentary": f"Task completion: {rate_text}. Plans without follow-through.",
    "wins": ["You showed up and journaled"],
    "failures": ["Tasks left incomplete", "Plans not followed"],
    "recurring_mistakes": ["Gliding instead of deep work", "Cheap dopamine"],
    "most_productive_day": "Unknown",
    "least_productive_day": "Unknown",
    "weekly_score": 50.0,
    "mentor_rule_for_next_week": "You will complete your first 3 tasks before any entertainment. No exceptions.",
    "one_percent_focus": "Lock in one deep work block daily before phone.",
    "confidence": 0.3,
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
