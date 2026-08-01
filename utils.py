"""App initialization and shared utilities."""

import logging
from functools import lru_cache

import streamlit as st

from components.layout import top_nav
from components.theme import THEME_CSS
from config.settings import settings
from database.migrations import run_migrations

logging.basicConfig(
  filename=settings.LOG_FILE,
  level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
  format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

_migrations_done = False


def apply_theme():
  """Inject GoalOS global styling."""
  st.markdown(THEME_CSS, unsafe_allow_html=True)


def configure_page(title: str, icon: str = "🎯", layout: str = "wide"):
  """Set page config then apply theme (must be first Streamlit calls)."""
  try:
    st.set_page_config(
      page_title=title,
      page_icon=icon,
      layout=layout,
      initial_sidebar_state="collapsed",
    )
  except Exception:
    pass
  apply_theme()
  top_nav()


def init_app():
  """Run DB migrations once per session."""
  global _migrations_done
  if not _migrations_done:
    run_migrations()
    _migrations_done = True


@lru_cache
def get_coach_service():
  from services.coach_service import CoachService
  return CoachService()
