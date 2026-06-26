"""Application configuration loaded from environment."""

import os
from pathlib import Path

from dotenv import load_dotenv

_BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(_BASE_DIR / ".env")


def _get_setting(name: str, default: str = "") -> str:
  """Read from env first, then Streamlit secrets when available."""
  value = os.getenv(name)
  if value:
    return value
  try:
    import streamlit as st
    secret_value = st.secrets.get(name)
    if secret_value is not None:
      return str(secret_value)
  except Exception:
    pass
  return default


class Settings:
  """Central configuration for GoalOS."""

  OPENROUTER_API_KEY: str = _get_setting("OPENROUTER_API_KEY", "")
  OPENROUTER_MODEL: str = _get_setting("OPENROUTER_MODEL", "anthropic/claude-sonnet-4")
  DB_PATH: str = _get_setting("DB_PATH", str(_BASE_DIR / "goalos.db"))
  CHROMA_PATH: str = _get_setting("CHROMA_PATH", str(_BASE_DIR / "chroma_db"))
  LOG_LEVEL: str = _get_setting("LOG_LEVEL", "INFO")
  LOG_FILE: str = str(_BASE_DIR / "goalos.log")


settings = Settings()
