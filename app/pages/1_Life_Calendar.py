"""70-Year Life Weeks Visualizer and Strategic Horizon Alignment."""

import os
import sys
from datetime import date

_APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _APP_DIR not in sys.path:
  sys.path.insert(0, _APP_DIR)
import bootstrap  # noqa: F401
import streamlit as st

from components.layout import hero_card, info_card, page_header, section, stat_card
from database.connection import get_db
from database.repositories._helpers import row_to_dict
from database.repositories.goal_repository import GoalRepository
from services.life_calendar_service import LifeCalendarService
from utils import configure_page, init_app

configure_page("Life Calendar | GoalOS", "⏳")
init_app()

page_header("Life Calendar", "70-Year Perspective (Weeks Visualizer)")

with get_db() as conn:
  user_row = conn.execute("SELECT * FROM user WHERE id = 1").fetchone()
  user_data = row_to_dict(user_row) if user_row else {}

birth_date_str = user_data.get("birth_date") or "2002-06-17"
target_age = int(user_data.get("target_age") or 70)

try:
  birth_date = date.fromisoformat(birth_date_str)
except ValueError:
  birth_date = date(2002, 6, 17)

life_service = LifeCalendarService(birth_date=birth_date, target_age=target_age)
summary = life_service.get_summary()

c1, c2, c3, c4 = st.columns(4)
with c1:
  stat_card("Age", f"{summary['age_years']} yrs")
with c2:
  stat_card("Weeks Lived", f"{summary['weeks_lived']:,}")
with c3:
  stat_card("Weeks Remaining", f"{summary['weeks_remaining']:,}")
with c4:
  stat_card("Life Spent", f"{summary['percentage_lived']}%")

st.progress(min(1.0, summary["percentage_lived"] / 100.0))

section("70-Year Visual Life Grid (52 Weeks / Row)")
st.caption("Hover over any box to see the exact age and week index. Green = Lived, Glowing Gold = Current Week, Gray = Future.")

grid_data = life_service.get_grid_data()

st.markdown("""
<style>
.life-grid-container {
    background: #ffffff;
    border: 1px solid #e4e4e7;
    border-radius: 16px;
    padding: 1.25rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.04);
}
.life-grid {
    display: flex;
    flex-direction: column;
    gap: 3px;
    margin-top: 10px;
    font-family: 'Inter', system-ui, sans-serif;
}
.year-row {
    display: flex;
    align-items: center;
    gap: 3px;
}
.year-row.decade-row {
    margin-top: 6px;
    padding-top: 4px;
    border-top: 1px dashed #e4e4e7;
}
.year-label {
    width: 55px;
    font-size: 11px;
    font-weight: 600;
    color: #71717a;
    text-align: right;
    padding-right: 8px;
}
.decade-label {
    color: #4f46e5 !important;
    font-weight: 700 !important;
}
.week-box {
    width: 9px;
    height: 9px;
    border-radius: 2px;
    transition: transform 0.15s ease, filter 0.15s ease;
}
.week-box:hover {
    transform: scale(1.6);
    z-index: 10;
    cursor: pointer;
}
.week-past {
    background-color: #059669;
    opacity: 0.85;
}
.week-current {
    background-color: #f59e0b;
    box-shadow: 0 0 8px #f59e0b;
    transform: scale(1.4);
    z-index: 5;
}
.week-future {
    background-color: #e4e4e7;
    opacity: 0.6;
}
.grid-legend {
    display: flex;
    gap: 20px;
    margin-bottom: 12px;
    font-size: 13px;
    font-weight: 500;
}
.legend-item {
    display: flex;
    align-items: center;
    gap: 6px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="grid-legend">
    <div class="legend-item"><div class="week-box week-past"></div> <span>Past Weeks</span></div>
    <div class="legend-item"><div class="week-box week-current"></div> <span>Current Week</span></div>
    <div class="legend-item"><div class="week-box week-future"></div> <span>Future Weeks</span></div>
</div>
""", unsafe_allow_html=True)

html_rows = []
for row in grid_data:
  is_decade = (row["age"] % 10 == 0) and (row["age"] > 0)
  decade_cls = "decade-row" if is_decade else ""
  label_cls = "decade-label" if is_decade or row["age"] == 0 else ""

  boxes = []
  for w in row["weeks"]:
    cls = f"week-{w['status']}"
    title = f"Age {w['year']}, Week {w['week_of_year']} (Week #{w['global_week']})"
    boxes.append(f'<div class="week-box {cls}" title="{title}"></div>')

  html_rows.append(f"""
  <div class="year-row {decade_cls}">
    <div class="year-label {label_cls}">Age {row['age']:02d}</div>
    {''.join(boxes)}
  </div>
  """)

st.markdown(f'<div class="life-grid-container"><div class="life-grid">{"".join(html_rows)}</div></div>', unsafe_allow_html=True)

section("Goal Horizons Alignment")
goal_repo = GoalRepository()
active_goals = goal_repo.get_active()

if active_goals:
  st.caption("Active goals mapped against your 70-year life horizon")
  for goal in active_goals:
    hero_card(f"[{goal.horizon.upper()}] {goal.title}", f"Category: {goal.category} · Priority: {goal.priority} · Deadline: {goal.deadline or 'Open'}")
else:
  info_card("No active goals set. Define 5-year and 1-year goals on the Vision & Goals page.", "info")

with st.expander("⚙️ Adjust Birth Date & Life Expectancy"):
  with st.form("life_calendar_settings"):
    new_birth = st.date_input("Birth Date", value=birth_date)
    new_target_age = st.number_input("Target Life Expectancy (Years)", min_value=30, max_value=120, value=target_age)
    if st.form_submit_button("Update Life Settings"):
      with get_db() as conn:
        conn.execute("UPDATE user SET birth_date = ?, target_age = ? WHERE id = 1", (new_birth.isoformat(), int(new_target_age)))
      st.success("Life Calendar updated!")
      st.rerun()
