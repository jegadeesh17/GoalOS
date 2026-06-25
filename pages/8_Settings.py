"""Settings page."""

import os
import shutil
from pathlib import Path

import streamlit as st

from components.layout import page_header, section, stat_card
from config.settings import settings
from database.migrations import run_migrations
from database.repositories.coach_repository import CoachRepository
from database.repositories.goal_repository import GoalRepository
from database.repositories.log_repository import LogRepository
from database.repositories.memory_repository import MemoryRepository
from utils import configure_page, init_app

configure_page("Settings | GoalOS", "⚙️")
init_app()

page_header("Settings", "Configure AI and manage your local data.")

section("OpenRouter")
with st.container(border=True):
  model = st.text_input("Model", value=settings.OPENROUTER_MODEL)
  api_key = st.text_input("API Key", value=settings.OPENROUTER_API_KEY, type="password")
  if st.button("Save Settings", type="primary"):
    env_path = Path(__file__).resolve().parent.parent / ".env"
    lines = env_path.read_text().splitlines() if env_path.exists() else []
    updated = {"OPENROUTER_MODEL": model, "OPENROUTER_API_KEY": api_key}
    new_lines = []
    found = set()
    for line in lines:
      key = line.split("=")[0] if "=" in line else ""
      if key in updated:
        new_lines.append(f"{key}={updated[key]}")
        found.add(key)
      else:
        new_lines.append(line)
    for key, val in updated.items():
      if key not in found:
        new_lines.append(f"{key}={val}")
    env_path.write_text("\n".join(new_lines) + "\n")
    st.toast("Settings saved. Restart the app to apply.", icon="✅")

section("Database")
log_repo = LogRepository()
goal_repo = GoalRepository()
memory_repo = MemoryRepository()
coach_repo = CoachRepository()

c1, c2, c3, c4 = st.columns(4)
with c1:
  stat_card("Daily Logs", log_repo.count())
with c2:
  stat_card("Goals", goal_repo.count())
with c3:
  stat_card("Memories", memory_repo.count())
with c4:
  stat_card("Coach Sessions", coach_repo.count())

section("Danger Zone")
with st.container(border=True):
  st.caption("This permanently deletes all your data.")
  if st.button("Clear All Data", type="primary"):
    confirm = st.checkbox("I understand this cannot be undone")
    if confirm:
      if os.path.exists(settings.DB_PATH):
        os.remove(settings.DB_PATH)
      if os.path.exists(settings.CHROMA_PATH):
        shutil.rmtree(settings.CHROMA_PATH)
      run_migrations()
      st.toast("All data cleared.", icon="✅")
      st.rerun()
