"""GoalOS dashboard with explainable progress evidence."""

import json
from datetime import date, timedelta

import bootstrap  # noqa: F401
import streamlit as st

from components.layout import empty_state, hero_card, info_card, mentor_panel, page_header, section, stat_card
from database.repositories.goal_repository import GoalRepository
from database.repositories.log_repository import LogRepository
from database.repositories.memory_repository import MemoryRepository
from database.repositories.score_repository import ScoreRepository
from services.journal_helpers import log_task_stats
from utils import configure_page, init_app

configure_page("GoalOS", "🎯")
init_app()

today = date.today()
log_repo, goal_repo = LogRepository(), GoalRepository()
memory_repo, score_repo = MemoryRepository(), ScoreRepository()
today_log = log_repo.get_by_date(today)
page_header("GoalOS", today.strftime("%A, %B %d"))

if not today_log or not today_log.morning_completed:
  if st.button("Open today's journal", type="primary"):
    st.switch_page("pages/3_Journal.py")

section("Today's rule")
mentor_rule = None
if today_log and today_log.morning_ai_output:
  try:
    mentor = json.loads(today_log.morning_ai_output)
    mentor_rule = mentor.get("mentor_rule")
    if mentor_rule:
      mentor_panel(mentor)
      evidence = mentor.get("evidence", [])
      if evidence:
        labels = [item.get("goal_title") or f"Memory #{item.get('memory_id')}" for item in evidence if item.get("goal_title") or item.get("memory_id")]
        if labels:
          st.caption("Evidence: " + ", ".join(labels))
  except json.JSONDecodeError:
    pass
if not mentor_rule:
  empty_state("No rule yet", "Complete the morning journal to create a goal-linked coaching rule.")

section("Today")
c1, c2, c3 = st.columns(3)
with c1:
  stat_card("Morning", "Complete" if today_log and today_log.morning_completed else "Not started")
with c2:
  stat_card("Evening", "Complete" if today_log and today_log.evening_completed else "Open")
with c3:
  if today_log and today_log.planned_tasks:
    tasks = log_task_stats(today_log)
    stat_card("Tasks", f"{tasks['completed']}/{tasks['total']}")
  else:
    stat_card("Tasks", "No data")
if today_log and today_log.morning_completed and not today_log.evening_completed:
  if st.button("Close the day", use_container_width=True):
    st.switch_page("pages/3_Journal.py")

section("Consistency")
logs = log_repo.get_recent(60)
streak, expected = 0, today
for log in sorted(logs, key=lambda item: item.date, reverse=True):
  if log.date == expected and (log.morning_completed or log.evening_completed):
    streak += 1
    expected -= timedelta(days=1)
  else:
    break
stat_card("Day streak", streak)

section("Progress evidence")
scores = score_repo.get_recent(14)
goals = goal_repo.get_active()
commitments = memory_repo.get_by_type("commitment", status="active")
c1, c2, c3 = st.columns(3)
with c1:
  stat_card("Active goals", len(goals))
with c2:
  stat_card("Open commitments", len(commitments))
with c3:
  closed = sum(1 for log in logs[:7] if log.evening_completed)
  stat_card("Closed days (7d)", f"{closed}/{min(len(logs), 7)}" if logs else "No data")
if scores:
  st.caption("Overall growth score across calculated days")
  st.line_chart({"overall growth": [score.overall_growth_score or 0 for score in reversed(scores)]})
else:
  info_card("No calculated score trend yet. Close a day to establish a baseline.", "default")
if goals:
  st.caption("Goal pace")
  st.dataframe([{"goal": goal.title, "progress": f"{goal.progress * 100:.0f}%", "deadline": goal.deadline or "No deadline"} for goal in goals], hide_index=True, use_container_width=True)
if today_log and today_log.mood_morning:
  hero_card("Morning context", f"Sleep {today_log.sleep_hours or 'unknown'} hours · mood {today_log.mood_morning}/5")
