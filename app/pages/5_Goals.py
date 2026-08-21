"""Goals and Strategic Vision Page — 1-Month, 1-Year, 5-Year & 10-Year Horizons."""

import os
import sys

_APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _APP_DIR not in sys.path:
  sys.path.insert(0, _APP_DIR)
import bootstrap  # noqa: F401
import streamlit as st

from components.layout import info_card, page_header, section
from database.connection import get_db
from database.repositories.goal_repository import GoalRepository
from models.goal import GoalCreate, GoalUpdate
from utils import configure_page, init_app

configure_page("Goals | GoalOS", "🎯")
init_app()

page_header("Goals & Visions", "1-Month, 1-Year, 5-Year & 10-Year Horizons")

goal_repo = GoalRepository()
categorized = goal_repo.get_by_horizons()


def _render_goal_card(g):
  with st.expander(f"📌 {g.title} (Priority {g.priority}) — Progress: {g.progress * 100:.0f}%", expanded=True):
    col_info, col_actions = st.columns([2.5, 1])
    with col_info:
      st.write(f"**Category:** {g.category.title()} · **Horizon:** {g.horizon.upper()} · **Status:** {g.status.title()}")
      st.write(f"**Deadline:** {g.deadline or 'No deadline set'}")
      why_text = getattr(g, "reason", None) or getattr(g, "description", None)
      if why_text:
        st.info(f"**Why / Reason:** {why_text}")

    with col_actions:
      st.markdown("##### Quick Actions")
      col_btn1, col_btn2 = st.columns(2)
      with col_btn1:
        show_edit = st.checkbox("✏️ Edit", key=f"toggle_edit_{g.id}")
      with col_btn2:
        if st.button("🗑️ Delete", key=f"delete_goal_{g.id}"):
          goal_repo.delete(g.id)
          st.toast(f"Deleted '{g.title}'!", icon="🗑️")
          st.rerun()

    if show_edit:
      st.markdown("---")
      st.markdown("### ✏️ Edit Goal Details")
      with st.form(f"edit_goal_form_{g.id}"):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
          new_title = st.text_input("Goal Title", value=g.title)
          cat_list = ["career", "health", "finance", "learning", "personal"]
          new_category = st.selectbox("Category", cat_list, index=cat_list.index(g.category) if g.category in cat_list else 0)
          new_status = st.selectbox("Status", ["active", "completed", "archived"], index=["active", "completed", "archived"].index(g.status) if g.status in ["active", "completed", "archived"] else 0)
        with col_f2:
          new_progress = st.slider("Progress %", 0, 100, int(g.progress * 100)) / 100.0
          new_priority = st.slider("Priority (1 = Highest)", 1, 5, g.priority)
          hor_list = ["1-month", "1-year", "5-year"]
          new_horizon = st.selectbox("Horizon", hor_list, index=hor_list.index(g.horizon) if g.horizon in hor_list else 0)

        new_reason = st.text_area("Reason / Why Statement", value=getattr(g, "reason", None) or getattr(g, "description", None) or "")

        if st.form_submit_button("Save Goal Changes", type="primary", use_container_width=True):
          goal_repo.update(g.id, GoalUpdate(
            title=new_title,
            category=new_category,
            horizon=new_horizon,
            progress=new_progress,
            priority=new_priority,
            status=new_status,
            reason=new_reason or None,
          ))
          st.toast("Goal updated successfully!", icon="✅")
          st.rerun()


tab_1m, tab_1y, tab_5y, tab_10y, tab_new = st.tabs([
  "🗓️ 1-Month Goals",
  "🎯 1-Year Goals",
  "🚀 5-Year Goals",
  "🌟 10-Year Life Vision",
  "➕ Add New Goal",
])

with tab_1m:
  section("Short-Term Operational Goals (1-Month Horizon)")
  goals_1m = categorized.get("1-month", [])
  if goals_1m:
    for g in goals_1m:
      _render_goal_card(g)
  else:
    info_card("No 1-Month goals set. Use the 'Add New Goal' tab to create short-term monthly goals.", "info")

with tab_1y:
  section("Annual Milestone Goals (1-Year Horizon)")
  goals_1y = categorized.get("1-year", [])
  if goals_1y:
    for g in goals_1y:
      _render_goal_card(g)
  else:
    info_card("No 1-Year goals set.", "info")

with tab_5y:
  section("Strategic Trajectory (5-Year Horizon)")
  goals_5y = categorized.get("5-year", [])
  if goals_5y:
    for g in goals_5y:
      _render_goal_card(g)
  else:
    info_card("No 5-Year goals set.", "info")

with tab_10y:
  section("Long-Term Life Vision (10-Year Horizon)")
  with get_db() as conn:
    user_row = conn.execute("SELECT * FROM user WHERE id = 1").fetchone()
    vision_10y = user_row["life_vision"] if user_row and "life_vision" in user_row.keys() else ""

  st.caption("Define your 10-year ultimate north star life vision.")
  new_vision = st.text_area("10-Year Life Vision Statement", value=vision_10y or "", height=150)
  if st.button("Save 10-Year Life Vision", type="primary"):
    with get_db() as conn:
      conn.execute("UPDATE user SET life_vision = ? WHERE id = 1", (new_vision,))
    st.toast("10-Year Life Vision saved!", icon="🌟")
    st.rerun()

with tab_new:
  section("Add Goal across Horizons")
  with st.form("create_goal_form"):
    title = st.text_input("Goal Title")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
      horizon = st.selectbox("Goal Horizon", ["1-month", "1-year", "5-year"], format_func=lambda x: x.upper())
      category = st.selectbox("Category", ["career", "health", "finance", "learning", "personal"])
    with col_c2:
      priority = st.slider("Priority (1 = Highest)", 1, 5, 1)
      progress_pct = st.slider("Initial Progress %", 0, 100, 0) / 100.0

    why = st.text_area("Why Statement (Motivation & Value)")
    deadline = st.date_input("Target Deadline (Optional)")

    if st.form_submit_button("Create Goal", type="primary"):
      if not title:
        st.warning("Please enter a goal title.")
      else:
        goal_repo.create(GoalCreate(
          title=title,
          horizon=horizon,
          category=category,
          priority=priority,
          progress=progress_pct,
          reason=why or None,
          deadline=deadline,
        ))
        st.success(f"Goal '{title}' created under {horizon.upper()} horizon with {int(progress_pct * 100)}% progress!")
        st.rerun()
