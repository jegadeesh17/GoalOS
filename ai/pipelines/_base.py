"""Shared pipeline utilities."""

import json
from pathlib import Path
from typing import Any

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(name: str) -> str:
  return (PROMPTS_DIR / f"{name}.txt").read_text(encoding="utf-8")


def format_context(context: dict[str, Any]) -> str:
  return json.dumps(context, indent=2, default=str)


_STATUS_LABEL = {"ahead": "Ahead of pace", "on_pace": "On pace", "behind": "Behind pace"}
_NO_CHECK_IN_NOTE = (
  "(No numeric check-in on these goals yet, so this reads your recent execution, not measured progress.)"
)


def _value(number: float, unit: str | None) -> str:
  return f"{number:g} {unit}".strip() if unit else f"{number:g}"


def _measured_line(p: dict) -> str | None:
  """One honest sentence for a goal's measured pace; None when there is nothing to say yet."""
  title, unit, status = p.get("title", "Goal"), p.get("metric_unit"), p.get("status")
  if status in _STATUS_LABEL:
    latest = p["latest"]
    expected = "on the path they wrote for it" if p.get("path") == "custom" else "expected"
    line = (
      f"{title}: {_STATUS_LABEL[status]}. Latest check-in {_value(latest['value'], unit)} ({latest['month']}) vs "
      f"{_value(p['expected_now'], unit)} {expected} by then, {p['pct_of_target']:g}% of the way to "
      f"{_value(p['target_value'], unit)}."
    )
    projection = p.get("projection")
    if projection:
      line += (
        f" On this trend you'd reach about {_value(projection['value_at_deadline'], unit)} by {p['deadline']}"
        f" ({'enough' if projection['on_track'] else 'short of the target'})."
      )
    return line
  if status == "baseline_only":
    return f"{title}: starting value recorded; one more check-in is needed to measure pace."
  if status == "no_check_ins":
    return f"{title}: has a target of {_value(p['target_value'], unit)} but no check-ins yet."
  return None


def _goal_pacing_lines(goal_pacing: list[dict] | None, horizon: str | None = None) -> tuple[list[str], list[str]]:
  """(measured lines, not-yet-measurable lines) for the given horizon, or every horizon if None."""
  measured: list[str] = []
  waiting: list[str] = []
  for p in goal_pacing or []:
    if horizon and p.get("horizon") != horizon:
      continue
    line = _measured_line(p)
    if line:
      (measured if p.get("status") in _STATUS_LABEL else waiting).append(line)
  return measured, waiting


def _attention_line(attention: list[dict] | None) -> str | None:
  """One sentence on which goals completed tasks went to, or why that cannot be said yet."""
  if not attention:
    return None
  window, as_of = attention[0]["window_days"], attention[0]["as_of"]
  if not any(row["done_30d"] for row in attention):
    return "No completed task is linked to a goal yet, so per-goal attention cannot be measured (link tasks on the Goals page)."
  moved = [f"{row['title']} {row['done_recent']}" for row in attention if row["done_recent"]]
  quiet = [
    f"{row['title']} ({'never' if row['days_quiet'] is None else str(row['days_quiet']) + ' days'})"
    for row in attention
    if not row["done_recent"]
  ]
  line = f"Completed tasks per goal in the {window} days to {as_of}: {', '.join(moved) or 'none'}."
  if quiet:
    line += f" Quiet: {', '.join(quiet)}."
  return line


def _saved_month_lines(history: list[dict] | None) -> list[str]:
  """Sentences quoting the saved monthly snapshots (this month vs the one before, plus the strongest lever)."""
  if not history:
    return []
  current = history[-1]
  rate = current["tasks"]["completion_rate"]
  if rate is None:
    return []
  provisional = (
    f" (provisional, data through {current['data_through']})" if current.get("status") == "provisional" else ""
  )
  if len(history) > 1 and history[-2]["tasks"]["completion_rate"] is not None:
    previous = history[-2]
    delta = current.get("delta_vs_previous", {}).get("completion_rate")
    change = f" ({delta:+.1f} points)" if delta is not None else ""
    lines = [
      f"Saved months: {previous['month']} {previous['tasks']['completion_rate']}% of tasks done -> "
      f"{current['month']} {rate}%{change}{provisional}."
    ]
  else:
    lines = [
      f"Saved month {current['month']}: {rate}% of tasks done "
      f"({current['tasks']['done']}/{current['tasks']['planned']}){provisional}."
    ]
  levers = [lv for lv in current.get("top_levers", []) if lv.get("contrast")]
  if levers:
    top = levers[0]
    lines.append(f"Strongest lever ({top['tier']}, n={top['n']}): {top['contrast']}. Association, not proof of cause.")
  return lines


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
    measured, waiting = _goal_pacing_lines(context.get("goal_pacing"), horizon_label)
    if measured:
      # A measured gap always wins over the task-completion heuristic below.
      return " ".join(measured + waiting)
    if avg_completion is None:
      reading = f"Not enough recent logs to evaluate pacing against: {goal_text}."
    elif avg_completion < 40:
      reading = f"Off pace — recent execution ({avg_completion:.0f}% task completion) is not compounding toward: {goal_text}."
    else:
      reading = f"On pace — {avg_completion:.0f}% recent task completion is compounding toward: {goal_text}."
    return " ".join([reading, *waiting, _NO_CHECK_IN_NOTE])

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

  saved = _saved_month_lines(context.get("monthly_history"))
  measured, waiting = _goal_pacing_lines(context.get("goal_pacing"))
  history_note = " ".join(saved + ["Yearly pacing: " + " ".join(measured + waiting)] if (measured or waiting) else saved)
  attention = _attention_line(context.get("goal_attention"))
  if attention:
    history_note = f"{history_note} {attention}".strip()
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

  if history_note:
    narrative = f"{narrative} {history_note}"

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
