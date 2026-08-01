"""GoalOS dashboard with Life Calendar and Weekly Sync focus."""

from datetime import date

import bootstrap  # noqa: F401
import streamlit as st

from components.layout import hero_card, info_card, page_header, section, stat_card
from database.connection import get_db
from database.repositories._helpers import row_to_dict
from database.repositories.goal_repository import GoalRepository
from services.life_calendar_service import LifeCalendarService
from services.weekly_sync_service import WeeklySyncService
from utils import configure_page, init_app

configure_page("GoalOS", "🎯")
init_app()

today = date.today()
goal_repo = GoalRepository()
sync_service = WeeklySyncService()

# Load user profile
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
life_summary = life_service.get_summary()

page_header("GoalOS", today.strftime("%A, %B %d, %Y"))

# Top Banner: Life Weeks
section("⏳ Life Weeks Progress (70-Year Perspective)")
c1, c2, c3, c4 = st.columns(4)
with c1:
  stat_card("Age", f"{life_summary['age_years']} yrs")
with c2:
  stat_card("Weeks Lived", f"{life_summary['weeks_lived']:,}")
with c3:
  stat_card("Weeks Remaining", f"{life_summary['weeks_remaining']:,}")
with c4:
  stat_card("Life Spent", f"{life_summary['percentage_lived']}%")

st.progress(min(1.0, life_summary["percentage_lived"] / 100.0))

if st.button("Open Life Calendar (Interactive 70-Year Grid)", type="primary", use_container_width=True):
  st.switch_page("pages/1_Life_Calendar.py")

# Section: Journal Sync & Monthly Progress
section("🔄 Journal Sync & Monthly Progress")
logs = sync_service.get_recent_sync_logs(1)

if logs:
  last_log = logs[0]
  hero_card(
    f"Latest Progress Sync ({last_log['week_start']})",
    f"Monthly Alignment Score: {last_log['goal_alignment_score']}% · Source: {last_log['source_type'].upper()}",
  )
  st.markdown(f"**Monthly Pacing Focus:**\n{last_log['next_week_focus']}")
else:
  info_card("No journal folder scan recorded yet. Import your handwritten journal images or CSV to sync progress.", "info")

if st.button("Open Journal Page (Batch / Image Upload)", use_container_width=True):
  st.switch_page("pages/2_Journal.py")

# Section: Goal Horizons
section("🎯 Active Goal Horizons")
goals = goal_repo.get_active()
if goals:
  st.caption("Active goals linked to your short-, mid-, and long-term milestones.")
  st.dataframe(
    [
      {
        "horizon": (goal.horizon or "medium").upper(),
        "goal": goal.title,
        "progress": f"{goal.progress * 100:.0f}%",
        "deadline": goal.deadline or "No deadline",
      }
      for goal in goals
    ],
    hide_index=True,
    use_container_width=True,
  )
else:
  info_card("No active goals found. Set up goals in Vision & Goals.", "default")
