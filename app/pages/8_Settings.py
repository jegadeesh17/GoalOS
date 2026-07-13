"""Settings, privacy consent, export, and safe local-data controls."""

import os
import sys
from pathlib import Path

_APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _APP_DIR not in sys.path:
  sys.path.insert(0, _APP_DIR)
import bootstrap  # noqa: F401

import streamlit as st

from ai.openrouter_client import OpenRouterClient
from components.layout import page_header, section, stat_card
from config.settings import settings
from database.migrations import run_migrations
from database.repositories.coach_repository import CoachRepository
from database.repositories.goal_repository import GoalRepository
from database.repositories.log_repository import LogRepository
from database.repositories.memory_repository import MemoryRepository
from services.data_portability_service import DataPortabilityService
from services.memory_service import clear_collection_cache
from services.settings_service import SettingsService
from utils import configure_page, init_app

configure_page("Settings | GoalOS", "⚙️")
init_app()
page_header("Settings", "Configure AI, privacy, and local data.")

settings_service = SettingsService()
portability = DataPortabilityService()

section("OpenRouter")
with st.container(border=True):
  model_options = [
    "anthropic/claude-sonnet-4", "meta-llama/llama-3.3-70b-instruct",
    "google/gemini-2.5-flash-preview", "openai/gpt-4o-mini",
    "meta-llama/llama-3.3-70b-instruct:free", "openai/gpt-oss-20b:free",
    "qwen/qwen3-coder:free", "meta-llama/llama-3.2-3b-instruct:free",
    "google/gemma-4-31b-it:free",
  ]
  st.caption("An API key enables remote AI only after you explicitly grant consent below.")
  model = st.selectbox("Model", model_options, index=model_options.index(settings.OPENROUTER_MODEL) if settings.OPENROUTER_MODEL in model_options else 0)
  api_key = st.text_input("API Key", value=settings.OPENROUTER_API_KEY, type="password")
  if st.button("Save model settings", type="primary"):
    env_path = Path(__file__).resolve().parent.parent / ".env"
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    updated = {"OPENROUTER_MODEL": model, "OPENROUTER_API_KEY": api_key}
    kept, found = [], set()
    for line in lines:
      key = line.split("=", 1)[0]
      if key in updated:
        kept.append(f"{key}={updated[key]}")
        found.add(key)
      else:
        kept.append(line)
    kept.extend(f"{key}={value}" for key, value in updated.items() if key not in found)
    env_path.write_text("\n".join(kept) + "\n", encoding="utf-8")
    st.toast("Model settings saved.", icon="✅")
    st.rerun()
  if st.button("Test OpenRouter connection", use_container_width=True):
    client = OpenRouterClient()
    client.refresh_config()
    with st.spinner("Calling OpenRouter..."):
      result = client.test_connection()
    if result.get("ok"):
      st.success(f"Working — {result['model']} replied: {result.get('reply', 'OK')}")
    else:
      st.error(f"Failed — {result.get('error')}: {result.get('detail', '')}")

section("Privacy")
with st.container(border=True):
  remote_ai_consent = st.checkbox(
    "Allow remote AI coaching", value=settings_service.remote_ai_allowed(),
    help="When enabled, selected journal context is sent to OpenRouter. Disabled uses local deterministic coaching only.",
  )
  if st.button("Save privacy preference", use_container_width=True):
    settings_service.set_remote_ai_allowed(remote_ai_consent)
    st.toast("Privacy preference saved.", icon="✅")
    st.rerun()
  if remote_ai_consent:
    st.warning("Remote AI may process selected journal context. Do not include credentials or highly sensitive information.")
  else:
    st.caption("Remote AI is disabled. Coaching remains local and deterministic.")

section("Database")
log_repo, goal_repo = LogRepository(), GoalRepository()
memory_repo, coach_repo = MemoryRepository(), CoachRepository()
c1, c2, c3, c4 = st.columns(4)
with c1:
  stat_card("Daily Logs", log_repo.count())
with c2:
  stat_card("Goals", goal_repo.count())
with c3:
  stat_card("Active Memories", memory_repo.count(status="active"))
with c4:
  stat_card("Coach Sessions", coach_repo.count())

section("Data export and reset")
with st.container(border=True):
  st.download_button("Download data export", data=portability.export_json(), file_name="goalos-export.json", mime="application/json", use_container_width=True)
  st.caption("Clearing creates a timestamped local backup first.")
  confirm = st.checkbox("I understand this clears active local data after creating a backup")
  if st.button("Clear All Data", type="primary", disabled=not confirm, use_container_width=True):
    try:
      backup = portability.clear_all_data()
      clear_collection_cache(settings.CHROMA_PATH)
      run_migrations()
      st.toast(f"All data cleared. Backup: {backup.name}", icon="✅")
      st.rerun()
    except Exception as exc:
      st.error(f"Data was not cleared because backup failed: {exc}")
