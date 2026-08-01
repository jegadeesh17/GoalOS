"""AI Coach Page — Goal & Progress Pacing AI Coaching."""

import json
import os
import sys
from datetime import date

_APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _APP_DIR not in sys.path:
  sys.path.insert(0, _APP_DIR)
import bootstrap  # noqa: F401
import streamlit as st

from components.layout import coaching_block, hero_card, info_card, mentor_panel, page_header, section, stat_card
from database.repositories.goal_repository import GoalRepository
from database.repositories.log_repository import LogRepository
from services.coach_service import CoachService
from services.weekly_sync_service import WeeklySyncService
from utils import configure_page, get_coach_service, init_app

configure_page("AI Coach | GoalOS", "🤖")
init_app()

today = date.today()
coach = get_coach_service()
goal_repo = GoalRepository()
log_repo = LogRepository()

page_header("AI Coach", "Personalized Coaching Based on Current Progress & Active Goals")

tab_progress, tab_rule, tab_chat = st.tabs([
  "🎯 Goal & Progress Coaching",
  "⚡ Today's Daily Rule",
  "💬 Interactive Coach Chat",
])

with tab_progress:
  section("Month-to-Date Progress Coaching")
  st.caption("AI evaluates your current month logged days, task execution, and 1-Month / 1-Year goals.")

  if st.button("Generate Goal & Progress Coaching", type="primary", use_container_width=True):
    with st.spinner("Analyzing progress, goal horizons, and vector memory..."):
      res = coach.get_progress_coaching(today)
      st.session_state["latest_ai_coach_res"] = res
      st.toast("Coaching generated!", icon="🔥")

  coaching = st.session_state.get("latest_ai_coach_res")
  if coaching:
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
      info_card(f"**Pacing Status:** {coaching.get('pacing_status', 'N/A')}", "accent")
    with col2:
      info_card(f"**1-Month Goal Evaluated:** {coaching.get('monthly_goal_evaluated', 'N/A')}", "success")

    hero_card("Execution Trajectory", coaching.get("progress_narrative", ""))

    c_a, c_b = st.columns(2)
    with c_a:
      section("Aligned Wins")
      st.write(coaching.get("key_wins_aligned", "N/A"))
    with c_b:
      section("Critical Bottleneck")
      st.write(coaching.get("critical_bottleneck", "N/A"))

    coaching_block("Actionable Coaching Advice", coaching.get("actionable_coaching_advice", ""))
  else:
    info_card("Click 'Generate Goal & Progress Coaching' above to evaluate your month-to-date trajectory against your goals.", "default")

with tab_rule:
  section("Today's Non-Negotiable Rule")
  log = log_repo.get_by_date(today)
  if not log:
    info_card("Log today's intention on the Journal page to receive today's rule.", "warning")
  else:
    if st.button("Issue Today's Mentor Rule"):
      with st.spinner("Issuing rule..."):
        rule_res = coach.get_morning_coaching(today, log)
        st.session_state["daily_rule_output"] = rule_res

    rule_out = st.session_state.get("daily_rule_output")
    if rule_out:
      mentor_panel(rule_out)

with tab_chat:
  section("Discuss Goals & Strategy with AI Coach")
  if "coach_chat_history" not in st.session_state:
    st.session_state.coach_chat_history = []

  for msg in st.session_state.coach_chat_history:
    with st.chat_message(msg["role"]):
      st.markdown(msg["content"])

  if prompt := st.chat_input("Ask your coach about goal pacing, habits, or bottlenecks..."):
    st.session_state.coach_chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
      st.markdown(prompt)

    with st.chat_message("assistant"):
      with st.spinner("Thinking..."):
        res = coach.chat(prompt, st.session_state.coach_chat_history)
        reply = res.get("response", "Keep pushing forward.")
        st.markdown(reply)
        st.session_state.coach_chat_history.append({"role": "assistant", "content": reply})
