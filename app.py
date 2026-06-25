"""GoalOS — dashboard landing: today's rule, status, streak."""

import json
from datetime import date, timedelta

import streamlit as st

from components.layout import empty_state, hero_card, info_card, page_header, section, stat_card
from database.repositories.log_repository import LogRepository
from services.journal_helpers import log_task_stats
from utils import configure_page, init_app

configure_page("GoalOS", "🎯")
init_app()

today = date.today()
log_repo = LogRepository()
today_log = log_repo.get_by_date(today)

page_header("GoalOS", today.strftime("%A, %B %d"))

if not today_log or not today_log.morning_completed:
  if st.button("Open Today's Journal", type="primary"):
    st.switch_page("pages/3_Journal.py")

section("Today's Rule")
mentor_rule = None
if today_log and today_log.morning_ai_output:
  try:
    output = json.loads(today_log.morning_ai_output)
    mentor_rule = output.get("mentor_rule")
    if mentor_rule:
      hero_card("Mentor Rule", mentor_rule)
      if output.get("past_mistake_called_out"):
        info_card(f"Pattern: {output['past_mistake_called_out']}", "warning")
  except json.JSONDecodeError:
    pass

if not mentor_rule:
  empty_state(
    "No rule yet",
    "Log your morning journal — tasks, sleep, mood — and your mentor will issue today's rule.",
  )

section("Today")
c1, c2, c3 = st.columns(3)
with c1:
  morning = "✅" if today_log and today_log.morning_completed else "—"
  stat_card("Morning", morning)
with c2:
  evening = "✅" if today_log and today_log.evening_completed else "—"
  stat_card("Evening", evening)
with c3:
  if today_log and today_log.evening_completed:
    stats = log_task_stats(today_log)
    stat_card("Tasks", f"{stats['completed']}/{stats['total']}" if stats["total"] else "—")
  elif today_log and today_log.planned_tasks:
    stats = log_task_stats(today_log)
    stat_card("Tasks planned", stats["total"])
  else:
    stat_card("Tasks", "—")

if today_log and today_log.mood_morning:
  st.caption(f"Sleep: {today_log.sleep_hours or '—'}h · Mood: {today_log.mood_morning}/5")

section("Streak")
logs = log_repo.get_recent(60)
streak = 0
expected = today
for log in sorted(logs, key=lambda x: x.date, reverse=True):
  if log.date == expected and (log.morning_completed or log.evening_completed):
    streak += 1
    expected -= timedelta(days=1)
  else:
    break
stat_card("Day streak", streak)

yesterday_log = log_repo.get_by_date(today - timedelta(days=1))
if yesterday_log and yesterday_log.takeaway:
  section("Yesterday's Takeaway")
  info_card(yesterday_log.takeaway, "accent")

if today_log and today_log.morning_completed and not today_log.evening_completed:
  if st.button("Close the day → Evening journal", use_container_width=True):
    st.switch_page("pages/3_Journal.py")
