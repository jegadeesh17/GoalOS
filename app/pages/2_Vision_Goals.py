"""Long-term goals — 1 year, 5 year, 10 year (equal priority for daily coaching)."""

import os
import sys

_APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _APP_DIR not in sys.path:
  sys.path.insert(0, _APP_DIR)
import bootstrap  # noqa: F401

import streamlit as st

from components.layout import info_card, page_header, section
from database.connection import get_db
from utils import configure_page, init_app

configure_page("Long-term Goals | GoalOS", "🎯")
init_app()

page_header(
  "Long-term Goals",
  "Fixed north stars. The mentor treats 1-year, 5-year, and 10-year goals with equal priority — every day should move all three forward.",
)

with get_db() as conn:
  user = conn.execute("SELECT * FROM user WHERE id = 1").fetchone()
user = dict(user) if user else {}

section("1-Year Goal")
one_year = st.text_area(
  "1-Year",
  value=user.get("one_year_vision") or "",
  height=100,
  label_visibility="collapsed",
  placeholder="What must be true in 1 year? Job, skills, income, health...",
)

section("5-Year Goal")
five_year = st.text_area(
  "5-Year",
  value=user.get("five_year_vision") or "",
  height=100,
  label_visibility="collapsed",
  placeholder="Where are you in 5 years?",
)

section("10-Year Goal")
ten_year = st.text_area(
  "10-Year",
  value=user.get("life_vision") or "",
  height=100,
  label_visibility="collapsed",
  placeholder="Who do you become in 10 years?",
)

if st.button("Save Goals", type="primary", use_container_width=True):
  with get_db() as conn:
    conn.execute(
      """UPDATE user SET
        one_year_vision = ?,
        five_year_vision = ?,
        life_vision = ?,
        updated_at = CURRENT_TIMESTAMP
      WHERE id = 1""",
      (one_year, five_year, ten_year),
    )
  st.toast("Goals saved. Your mentor will use these.", icon="✅")

info_card(
  "These goals don't change daily. Your journal and mentor rule exist to move you 1% closer to all three horizons — every day.",
  "accent",
)
