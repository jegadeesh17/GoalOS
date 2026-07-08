"""Weekly Review — task stats + mentor accountability."""

import os
import sys

_APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _APP_DIR not in sys.path:
  sys.path.insert(0, _APP_DIR)
import bootstrap  # noqa: F401

import json
from datetime import date, timedelta

import streamlit as st

from components.layout import coaching_block, empty_state, hero_card, info_card, page_header, section, stat_card
from database.connection import get_db
from database.repositories.log_repository import LogRepository
from services.journal_helpers import week_task_stats
from utils import configure_page, get_coach_service, init_app

configure_page("Weekly Review | GoalOS", "📊")
init_app()

page_header("Weekly Review", "Tasks planned vs done. Patterns called out. One rule for next week.")

today = date.today()
week_start = today - timedelta(days=today.weekday())
week_end = week_start + timedelta(days=6)
log_repo = LogRepository()
coach = get_coach_service()

week_logs = log_repo.get_range(week_start, week_end)
stats = week_task_stats(week_logs)

st.caption(f"Week of {week_start.strftime('%b %d')} – {week_end.strftime('%b %d')}")

section("Task Stats")
c1, c2, c3, c4 = st.columns(4)
with c1:
  stat_card("Days logged", stats["days_logged"])
with c2:
  stat_card("Tasks planned", stats["total_tasks"])
with c3:
  stat_card("Completed", stats["completed_tasks"])
with c4:
  rate = f"{stats['week_completion_rate']}%" if stats["week_completion_rate"] is not None else "—"
  stat_card("Completion", rate)

if stats["total_tasks"] == 0:
  info_card("No tasks logged this week. Use Today's Journal to track plans and tasks.", "warning")

with get_db() as conn:
  existing = conn.execute(
    "SELECT * FROM weekly_reviews WHERE week_start = ?", (week_start.isoformat(),)
  ).fetchone()

if existing and existing["ai_output"] and not st.session_state.get("regenerate_weekly"):
  output = json.loads(existing["ai_output"])
  hero_card("Week Summary", output.get("week_summary", ""))

  if output.get("task_stats_commentary"):
    coaching_block("On your numbers", output["task_stats_commentary"])

  col1, col2 = st.columns(2)
  with col1:
    section("Wins")
    for w in output.get("wins", []):
      info_card(w, "success")
  with col2:
    section("Failures")
    for f in output.get("failures", []):
      info_card(f, "danger")

  if output.get("recurring_mistakes"):
    section("Recurring Mistakes")
    for m in output["recurring_mistakes"]:
      info_card(m, "warning")

  if output.get("mentor_rule_for_next_week"):
    hero_card("Rule for Next Week", output["mentor_rule_for_next_week"])

  if output.get("one_percent_focus"):
    coaching_block("1% focus", output["one_percent_focus"])

  if st.button("Regenerate Review"):
    st.session_state.regenerate_weekly = True
    st.rerun()
else:
  if st.button("Generate Weekly Review", type="primary", use_container_width=True):
    if len(week_logs) < 1:
      empty_state("Not enough data", "Log at least one day this week in your journal.")
    else:
      with st.spinner("Mentor is reviewing your week..."):
        try:
          coach.get_weekly_coaching(week_start)
          st.session_state.regenerate_weekly = False
          st.toast("Weekly review ready.", icon="✅")
          st.rerun()
        except Exception as e:
          st.error(f"Weekly review failed: {e}")
  else:
    empty_state("Ready when you are", "Generate your review to see wins, failures, and next week's rule.")
