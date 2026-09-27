"""Shared pipeline utilities."""

import json
from pathlib import Path
from typing import Any

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(name: str) -> str:
  return (PROMPTS_DIR / f"{name}.txt").read_text(encoding="utf-8")


def format_context(context: dict[str, Any]) -> str:
  return json.dumps(context, indent=2, default=str)


def fallback_future_self(context: dict) -> dict:
  written_from_age = context.get("current_age_in_10_years")
  opener = (
    f"I'm you, {written_from_age} years old, writing back."
    if written_from_age is not None
    else "I'm you, ten years from now, writing back."
  )
  visions = context.get("user_vision") or {}
  five_year_goal = (visions.get("five_year_vision") or "").strip()
  ten_year_goal = (visions.get("ten_year_vision") or "").strip()

  recent_logs = context.get("recent_logs", [])
  rates = [l.get("task_completion_rate") for l in recent_logs if l.get("task_completion_rate") is not None]
  avg_completion = (sum(rates) / len(rates)) if rates else None

  def pacing_for(goal_text: str, horizon_label: str) -> str:
    if not goal_text:
      return f"No {horizon_label} goals defined yet - nothing to pace against."
    if avg_completion is None:
      return f"Not enough recent logs to evaluate pacing against: {goal_text}."
    if avg_completion < 40:
      return f"Off pace — recent execution ({avg_completion:.0f}% task completion) is not compounding toward: {goal_text}."
    return f"On pace — {avg_completion:.0f}% recent task completion is compounding toward: {goal_text}."

  five_year_pacing = pacing_for(five_year_goal, "5-year")
  ten_year_pacing = pacing_for(ten_year_goal, "10-year")

  defined_goals = [g for g in (five_year_goal, ten_year_goal) if g]
  goals_joined = " and ".join(defined_goals)
  are_or_is = "is" if len(defined_goals) == 1 else "are"

  if not defined_goals:
    message = (
      f"{opener} There's nothing on the Goals page yet for "
      "5 or 10 years out, so I can't tell you if today is building toward anything. Define them, then we can check."
    )
  elif avg_completion is None:
    message = (
      f"{opener} There isn't enough logged yet to tell you "
      "whether the days are adding up to anything. Start logging so future-you can actually check."
    )
  elif avg_completion < 40:
    message = (
      f"{opener} {goals_joined} {are_or_is} still just words "
      "right now, because the days aren't compounding toward them. Fix the follow-through, not the plan."
    )
  else:
    message = (
      f"{opener} What you're doing now is working — "
      f"{goals_joined} {are_or_is} becoming real because of days like these."
    )

  return {
    "message": message,
    "written_from_age": written_from_age,
    "five_year_pacing": five_year_pacing,
    "ten_year_pacing": ten_year_pacing,
    "key_things_referenced": defined_goals,
    "confidence": 0.5,
    "source": "heuristic_fallback",
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
