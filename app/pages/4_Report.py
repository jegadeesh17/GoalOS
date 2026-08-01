"""Report Page — Month-wise Goal vs. Performance Evaluation."""

import calendar
import os
import sys
from datetime import date, timedelta

_APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _APP_DIR not in sys.path:
  sys.path.insert(0, _APP_DIR)
import bootstrap  # noqa: F401
import streamlit as st

from components.layout import hero_card, info_card, page_header, section, stat_card
from database.repositories.goal_repository import GoalRepository
from database.repositories.log_repository import LogRepository
from services.weekly_sync_service import WeeklySyncService
from utils import configure_page, init_app

configure_page("Report | GoalOS", "📊")
init_app()

page_header("Report", "Month-wise Goal vs. Actual Performance Reports")

sync_service = WeeklySyncService()
log_repo = LogRepository()
goal_repo = GoalRepository()
active_goals = goal_repo.get_active()

all_logs = log_repo.get_all()

# Group all available logs by month
months_map = {}
for l in all_logs:
  d = l.date
  key = (d.year, d.month)
  if key not in months_map:
    m_start = d.replace(day=1)
    m_name = m_start.strftime("%B %Y")
    months_map[key] = {
      "key": key,
      "month_name": m_name,
      "month_start": m_start,
      "logs": [],
    }
  months_map[key]["logs"].append(l.model_dump(mode="json"))

# Ensure current month is included even if 0 logs
today = date.today()
curr_key = (today.year, today.month)
if curr_key not in months_map:
  curr_start = today.replace(day=1)
  months_map[curr_key] = {
    "key": curr_key,
    "month_name": curr_start.strftime("%B %Y"),
    "month_start": curr_start,
    "logs": [],
  }

# Order months by date desc (newest first)
sorted_months = sorted(months_map.values(), key=lambda m: m["key"], reverse=True)

section("🗓️ Select Month Report")
selected_month_name = st.selectbox(
  "Choose Month to Inspect",
  [f"{m['month_name']} ({len(m['logs'])} days logged)" for m in sorted_months],
  index=0,
)

# Extract selected month object
sel_index = [f"{m['month_name']} ({len(m['logs'])} days logged)" for m in sorted_months].index(selected_month_name)
sel_month = sorted_months[sel_index]

month_name = sel_month["month_name"]
month_start = sel_month["month_start"]
raw_logs = sel_month["logs"]

progress = sync_service.calculate_monthly_progress(raw_logs, month_start=month_start, month_name=month_name, active_goals=active_goals)
monthly_report = sync_service.generate_monthly_report(raw_logs, month_name=month_name, active_goals=active_goals, month_start=month_start)
yearly_report = sync_service.generate_yearly_report([monthly_report], year_name=str(month_start.year), active_goals=active_goals)

section(f"📈 {month_name} Overview")
c1, c2, c3, c4 = st.columns(4)
with c1:
  stat_card("Days Logged", f"{progress['days_logged']} / {progress['days_in_month']}")
with c2:
  stat_card("Logging Pacing", f"{progress.get('logging_consistency_rate', progress['monthly_completion_rate']):.1f}%")
with c3:
  stat_card("Task Execution", f"{progress.get('avg_task_execution_rate', 0.0):.1f}%")
with c4:
  stat_card("Overall Goal Alignment", f"{progress['monthly_completion_rate']:.1f}%")

st.progress(min(1.0, progress["monthly_completion_rate"] / 100.0))
info_card(f"**Pacing Verdict:** {progress['pacing_status']} — {progress['coaching_takeaway']}", "accent")

section("🎯 Month's Strengths, Weaknesses & 3-Step Action Plan")
col_str, col_weak = st.columns(2)
with col_str:
  hero_card("💪 Execution Strengths & Wins", f"Semantic Goal Alignment: {progress.get('semantic_goal_alignment', 50.0):.1f}%")
  info_card(f"**Target 1-Month Goal:** {progress['primary_monthly_goal']}", "default")
  info_card(f"**Key Strengths & Milestones:**\n{progress.get('strengths', progress['wins'])}", "success")

with col_weak:
  hero_card("⚠️ Bottlenecks & Friction Areas", f"Average Task Execution: {progress.get('avg_task_execution_rate', 0.0):.1f}%")
  info_card(f"**Distraction & Friction Patterns:**\n{progress.get('weaknesses', progress['takeaways'])}", "warning")

section("📋 3-Step Standard Action Plan for Next Month")
info_card(progress.get("takeaways_3step", "1. Focus on top priority task first\n2. Eliminate distractions during deep work\n3. Maintain daily consistency"), "info")

section("🔮 Cascading Goal Impact (1-Month ➔ 1-Year ➔ 5-Year)")
info_card(monthly_report.get("cascading_goal_impact", "High monthly consistency accelerates your long-term milestones."), "accent")


section(f"📊 Annual {month_start.year} Performance Synthesis")
with st.expander(f"Annual {yearly_report['year']} Execution Summary across Available Months", expanded=True):
  st.write(f"**Annual Alignment Score:** {yearly_report['annual_alignment_score']}%")
  st.write(f"**Annual Verdict:** {yearly_report['annual_verdict']}")
  st.write(f"**1-Year Target Goals:** " + ", ".join(yearly_report["one_year_goals"]))
  st.write(f"**5-Year Vision Goals:** " + ", ".join(yearly_report["five_year_goals"]))

