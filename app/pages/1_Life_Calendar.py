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

# Load user profile birth date & target age
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

# Top Metrics Row
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

section("Life Grid (70 Years × 52 Weeks)")
st.caption("Each row represents one year of life. Each box is 1 week. Green = Lived, Pulsing Gold = Current Week, Muted Gray = Future.")

grid_data = life_service.get_grid_data()

# Custom CSS for rendering lightweight responsive grid
st.markdown("""
<style>
.life-grid {
    display: flex;
    flex-direction: column;
    gap: 3px;
    margin-top: 15px;
    font-family: monospace;
}
.year-row {
    display: flex;
    align-items: center;
    gap: 2px;
}
.year-label {
    width: 55px;
    font-size: 11px;
    color: #888;
    text-align: right;
    padding-right: 6px;
}
.week-box {
    width: 9px;
    height: 9px;
    border-radius: 2px;
}
.week-past {
    background-color: #2e7d32;
    opacity: 0.85;
}
.week-current {
    background-color: #ffb300;
    box-shadow: 0 0 6px #ffb300;
    transform: scale(1.3);
    z-index: 2;
}
.week-future {
    background-color: #333333;
    opacity: 0.35;
}
.grid-legend {
    display: flex;
    gap: 15px;
    margin-bottom: 10px;
    font-size: 13px;
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

# Render compact grid container
html_rows = []
for row in grid_data:
  boxes = []
  for w in row["weeks"]:
    cls = f"week-{w['status']}"
    title = f"Age {w['year']}, Week {w['week_of_year']} (Week #{w['global_week']})"
    boxes.append(f'<div class="week-box {cls}" title="{title}"></div>')
  
  html_rows.append(f"""
  <div class="year-row">
    <div class="year-label">Age {row['age']:02d}</div>
    {''.join(boxes)}
  </div>
  """)

st.markdown(f'<div class="life-grid">{"".join(html_rows)}</div>', unsafe_allow_html=True)

section("Goal Horizons Alignment")
goal_repo = GoalRepository()
active_goals = goal_repo.get_active()

if active_goals:
  st.caption("Active goals mapped against your life horizon")
  for goal in active_goals:
    hero_card(f"[{goal.horizon.upper()}] {goal.title}", f"Category: {goal.category} · Priority: {goal.priority} · Deadline: {goal.deadline or 'Open'}")
else:
  info_card("No active goals set. Define 5-year and 1-year goals on the Vision & Goals page.", "info")

# Settings Expander
with st.expander("⚙️ Adjust Birth Date & Life Expectancy"):
  with st.form("life_calendar_settings"):
    new_birth = st.date_input("Birth Date", value=birth_date)
    new_target_age = st.number_input("Target Life Expectancy (Years)", min_value=30, max_value=120, value=target_age)
    if st.form_submit_button("Update Life Settings"):
      with get_db() as conn:
        conn.execute("UPDATE user SET birth_date = ?, target_age = ? WHERE id = 1", (new_birth.isoformat(), int(new_target_age)))
      st.success("Life Calendar updated!")
      st.rerun()
