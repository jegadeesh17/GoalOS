"""Settings page."""

import os
import shutil
from pathlib import Path

import streamlit as st

from components.layout import page_header, section, stat_card
from ai.openrouter_client import OpenRouterClient
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
  if settings.OPENROUTER_API_KEY:
    st.success("API key configured — mentor uses AI + your journal data.")
  else:
    st.warning("No API key — mentor uses journal-based rules only. Add a key for full AI personalization.")
  model = st.selectbox(
    "Model",
    options=[
      "anthropic/claude-sonnet-4",
      "meta-llama/llama-3.3-70b-instruct",
      "google/gemini-2.5-flash-preview",
      "openai/gpt-4o-mini",
    ],
    index=0 if settings.OPENROUTER_MODEL not in [
      "anthropic/claude-sonnet-4",
      "meta-llama/llama-3.3-70b-instruct",
      "google/gemini-2.5-flash-preview",
      "openai/gpt-4o-mini",
    ] else [
      "anthropic/claude-sonnet-4",
      "meta-llama/llama-3.3-70b-instruct",
      "google/gemini-2.5-flash-preview",
      "openai/gpt-4o-mini",
    ].index(settings.OPENROUTER_MODEL),
    help="claude-3.5-sonnet is retired on OpenRouter — use claude-sonnet-4",
  )
  if settings.OPENROUTER_MODEL == "anthropic/claude-3.5-sonnet":
    st.error("Your model anthropic/claude-3.5-sonnet is retired. Save with claude-sonnet-4 selected.")
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
    st.toast("Settings saved.", icon="✅")
    st.rerun()

  if st.button("Test OpenRouter connection", use_container_width=True):
    client = OpenRouterClient()
    client.refresh_config()
    with st.spinner("Calling OpenRouter..."):
      result = client.test_connection()
    if result.get("ok"):
      st.success(f"Working — model `{result['model']}` replied: \"{result.get('reply', 'OK')}\"")
    else:
      st.error(f"Failed — {result.get('error')}: {result.get('detail', '')}")

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
