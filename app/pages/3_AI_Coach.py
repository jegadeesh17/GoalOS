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

from components.layout import coaching_block, hero_card, info_card, mentor_panel, page_header, pattern_block, section, stat_card
from database.repositories.goal_repository import GoalRepository
from database.repositories.log_repository import LogRepository
from services.coach_service import CoachService
from services.pattern_service import PatternService
from services.weekly_sync_service import WeeklySyncService
from utils import configure_page, get_coach_service, init_app

configure_page("AI Coach | GoalOS", "🤖")
init_app()

today = date.today()
coach = get_coach_service()
goal_repo = GoalRepository()
log_repo = LogRepository()

page_header("AI Coach", "Pattern-Focused Coaching & Goal Pacing Evaluation")

tab_progress, tab_rule, tab_chat = st.tabs([
  "🎯 Goal & Progress Coaching",
  "⚡ Today's Daily Rule",
  "💬 Interactive Coach Chat",
])

with tab_progress:
  section("Month-to-Date Progress & Pattern Coaching")
  st.caption("AI prioritizes repeating behavioral patterns over 1-day noise to safeguard your 1-Month and 1-Year goals.")

  if st.button("Generate Goal & Progress Coaching", type="primary", use_container_width=True):
    with st.spinner("Analyzing multi-day patterns, goal horizons, and vector memory..."):
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

    # Pattern Recognition vs 1-Day Noise Block
    pattern_text = coaching.get("recognized_pattern_analysis")
    if pattern_text:
      pattern_block("Recognized Behavioral Pattern Analysis (Chronic vs 1-Day Noise)", pattern_text, "warning")

    protocol_text = coaching.get("actionable_pattern_breaking_protocol")
    if protocol_text:
      pattern_block("Actionable Pattern-Breaking Protocol", protocol_text, "accent")

    c_a, c_b = st.columns(2)
    with c_a:
      section("Aligned Wins & Compounding Habits")
      st.write(coaching.get("key_wins_aligned", "N/A"))
    with c_b:
      section("Critical Bottleneck")
      st.write(coaching.get("critical_bottleneck", "N/A"))

    coaching_block("Actionable Coaching Advice", coaching.get("actionable_coaching_advice", ""))

    # Multi-day pattern telemetry expander
    recent_logs = log_repo.get_recent(21)
    if recent_logs:
      p_report = PatternService().analyze_patterns(recent_logs, target_date=today)
      with st.expander("🔍 Multi-Day Pattern Recognition Telemetry", expanded=False):
        st.caption(f"Analyzed {p_report['total_logs_analyzed']} daily logs for repeating behavioral loops.")
        repeating = p_report.get("repeating_unhealthy_patterns", [])
        if repeating:
          st.markdown("#### 🚨 Repeating Unhealthy Patterns (2+ Occurrences)")
          for p in repeating:
            dates = ", ".join(p.get("dates_observed", []))
            st.markdown(f"- **{p['pattern_name']}** ({p['occurrences_count']}x — Dates: `{dates}`)")
            st.markdown(f"  *Root Trigger:* {p['root_trigger']}")
            st.markdown(f"  *Protocol:* {p['actionable_countermeasure']}")
        else:
          st.success("No repeating unhealthy patterns detected in recent logs!")
        
        isolated = p_report.get("isolated_friction_events", [])
        if isolated:
          st.markdown("#### ℹ️ Isolated 1-Day Events (Noise, Not Chronic)")
          for iso in isolated:
            st.markdown(f"- **{iso['event_name']}** on `{iso['date_observed']}` — *{iso['reset_advice']}*")
  else:
    info_card("Click 'Generate Goal & Progress Coaching' above to evaluate your multi-day patterns and goal trajectory.", "default")

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
