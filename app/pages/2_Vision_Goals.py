"""Vision, measurable goals, and milestones."""

import os
import sys
from datetime import date

_APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _APP_DIR not in sys.path:
  sys.path.insert(0, _APP_DIR)
import bootstrap  # noqa: F401

import streamlit as st

from components.goal_card import render_goal_card
from components.layout import info_card, page_header, section
from database.connection import get_db
from database.repositories.goal_repository import GoalRepository
from database.repositories.milestone_repository import MilestoneRepository
from models.goal import GoalCreate, GoalUpdate
from models.milestone import MilestoneCreate, MilestoneUpdate
from utils import configure_page, init_app

configure_page("Long-term Goals | GoalOS", "🎯")
init_app()
page_header("Long-term Goals", "Turn your north stars into measurable goals, milestones, and daily evidence.")

goal_repo, milestone_repo = GoalRepository(), MilestoneRepository()
with get_db() as conn:
  row = conn.execute("SELECT * FROM user WHERE id = 1").fetchone()
user = dict(row) if row else {}

with st.expander("Vision horizons", expanded=not any(user.get(key) for key in ("one_year_vision", "five_year_vision", "life_vision"))):
  one_year = st.text_area("1-year vision", value=user.get("one_year_vision") or "", height=90)
  five_year = st.text_area("5-year vision", value=user.get("five_year_vision") or "", height=90)
  ten_year = st.text_area("10-year vision", value=user.get("life_vision") or "", height=90)
  if st.button("Save visions", type="primary"):
    with get_db() as conn:
      conn.execute("UPDATE user SET one_year_vision=?, five_year_vision=?, life_vision=?, updated_at=CURRENT_TIMESTAMP WHERE id=1", (one_year, five_year, ten_year))
    st.toast("Visions saved.", icon="✅")

section("Create a measurable goal")
with st.form("new_goal", clear_on_submit=True):
  title = st.text_input("Goal title")
  c1, c2, c3 = st.columns(3)
  with c1:
    category = st.selectbox("Category", ["career", "health", "learning", "personal", "financial"])
  with c2:
    horizon = st.selectbox("Horizon", ["quarterly", "yearly", "five_year", "ten_year"])
  with c3:
    priority = st.slider("Priority", 1, 5, 3)
  deadline = st.date_input("Deadline", value=None)
  success_criteria = st.text_area("Success criteria", placeholder="What observable result proves this goal is complete?")
  if st.form_submit_button("Create goal"):
    if not title.strip():
      st.error("A goal title is required.")
    else:
      goal_repo.create(GoalCreate(title=title, category=category, horizon=horizon, priority=priority, deadline=deadline, success_criteria=success_criteria or None))
      st.rerun()

section("Goals and milestones")
goals = goal_repo.get_active()
if not goals:
  info_card("Start with one measurable goal. You can link today’s tasks to it immediately.", "accent")
for goal in goals:
  render_goal_card(goal)
  with st.expander(f"Manage: {goal.title}"):
    progress = st.slider("Goal progress", 0.0, 1.0, float(goal.progress), 0.05, key=f"goal_progress_{goal.id}")
    status = st.selectbox("Goal status", ["active", "completed", "archived"], index=["active", "completed", "archived"].index(goal.status) if goal.status in ("active", "completed", "archived") else 0, key=f"goal_status_{goal.id}")
    if st.button("Save goal progress", key=f"save_goal_{goal.id}"):
      goal_repo.update(goal.id, GoalUpdate(progress=progress, status=status))
      st.rerun()
    milestones = milestone_repo.get_for_goal(goal.id, include_archived=True)
    for milestone in milestones:
      cols = st.columns([4, 2, 2])
      with cols[0]:
        st.write(milestone.title)
        if milestone.success_criteria:
          st.caption(milestone.success_criteria)
      with cols[1]:
        milestone_progress = st.slider("Progress", 0.0, 1.0, float(milestone.progress), 0.05, key=f"milestone_progress_{milestone.id}")
      with cols[2]:
        milestone_status = st.selectbox("Status", ["active", "completed", "archived"], index=["active", "completed", "archived"].index(milestone.status), key=f"milestone_status_{milestone.id}")
      if st.button("Save milestone", key=f"save_milestone_{milestone.id}"):
        milestone_repo.update(milestone.id, MilestoneUpdate(progress=milestone_progress, status=milestone_status))
        st.rerun()
    with st.form(f"new_milestone_{goal.id}", clear_on_submit=True):
      milestone_title = st.text_input("New milestone", key=f"milestone_title_{goal.id}")
      milestone_criteria = st.text_input("Completion evidence", key=f"milestone_criteria_{goal.id}")
      milestone_deadline = st.date_input("Milestone deadline", value=None, key=f"milestone_deadline_{goal.id}")
      if st.form_submit_button("Add milestone"):
        if milestone_title.strip():
          milestone_repo.create(MilestoneCreate(goal_id=goal.id, title=milestone_title, success_criteria=milestone_criteria or None, deadline=milestone_deadline))
          st.rerun()
        else:
          st.error("A milestone title is required.")
