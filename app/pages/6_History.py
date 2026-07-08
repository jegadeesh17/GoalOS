"""History page with import and semantic search."""

import os
import sys

_APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _APP_DIR not in sys.path:
  sys.path.insert(0, _APP_DIR)
import bootstrap  # noqa: F401

import json
import tempfile
from datetime import date
from pathlib import Path

import streamlit as st

from components.layout import empty_state, page_header, section, stat_card
from components.memory_card import render_memory_card
from components.timeline_entry import render_timeline_entry
from database.connection import get_db
from database.repositories.coach_repository import CoachRepository
from database.repositories.log_repository import LogRepository
from database.repositories.memory_repository import MemoryRepository
from services.journal_import_service import JournalImportService
from services.memory_service import MemoryService
from utils import configure_page, init_app

configure_page("History | GoalOS", "📜")
init_app()

page_header("History", "Past journals and imported entries.")

log_repo = LogRepository()
memory_repo = MemoryRepository()
coach_repo = CoachRepository()
memory_service = MemoryService()
import_service = JournalImportService()

# Stats
c1, c2, c3 = st.columns(3)
with c1:
  stat_card("Daily Logs", log_repo.count())
with c2:
  stat_card("Memories", memory_repo.count())
with c3:
  stat_card("Coach Sessions", coach_repo.count())

with st.expander("Import Journal Data", expanded=False):
  tab1, tab2, tab3 = st.tabs(["Excel", "JSON", "Paste Text"])
  with tab1:
    uploaded = st.file_uploader("Upload Excel file", type=["xlsx", "xls", "csv"])
    if uploaded and st.button("Import Excel", type="primary"):
      with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as f:
        f.write(uploaded.getvalue())
        tmp_path = f.name
      with st.spinner("Importing..."):
        result = import_service.import_from_excel(tmp_path)
        Path(tmp_path).unlink(missing_ok=True)
        st.toast(f"Imported {result.successfully_imported}/{result.total_entries} entries", icon="✅")
        if result.errors:
          st.warning("Errors: " + "; ".join(result.errors[:5]))
        if result.onboarding_summary:
          st.session_state.onboarding_summary = result.onboarding_summary
        st.rerun()

  with tab2:
    json_upload = st.file_uploader("Upload JSON file", type=["json"])
    if json_upload and st.button("Import JSON", type="primary"):
      with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
        f.write(json_upload.getvalue())
        tmp_path = f.name
      with st.spinner("Importing..."):
        result = import_service.import_from_json(tmp_path)
        Path(tmp_path).unlink(missing_ok=True)
        st.toast(f"Imported {result.successfully_imported}/{result.total_entries} entries", icon="✅")
        if result.errors:
          st.warning("Errors: " + "; ".join(result.errors[:5]))
        if result.onboarding_summary:
          st.session_state.onboarding_summary = result.onboarding_summary
        st.rerun()

  with tab3:
    raw_text = st.text_area("Paste journal text", height=300, label_visibility="collapsed")
    if raw_text and st.button("Import Text", type="primary"):
      with st.spinner("Parsing and importing..."):
        result = import_service.import_from_text_block(raw_text)
        st.toast(f"Imported {result.successfully_imported} entries", icon="✅")
        if result.errors:
          st.warning("Errors: " + "; ".join(result.errors[:5]))
        if result.onboarding_summary:
          st.session_state.onboarding_summary = result.onboarding_summary
        st.rerun()

summary = st.session_state.get("onboarding_summary") or import_service.generate_onboarding_summary()
if "No journal entries" not in summary:
  section("Onboarding Summary")
  st.markdown(summary)

section("Search")
col1, col2 = st.columns([3, 1])
search_query = col1.text_input("Semantic search", placeholder="Search memories and journals...", label_visibility="collapsed")
filter_type = col2.selectbox("Filter", ["all", "log", "weekly", "memory", "coaching"], label_visibility="collapsed")

if search_query:
  with st.spinner("Searching..."):
    results = memory_service.retrieve(search_query, top_k=10)
    if results:
      for mem in results:
        render_memory_card(mem)
    else:
      empty_state("No results", "Try different keywords.")

section("Timeline")
logs = log_repo.get_all()

if filter_type in ("all", "log"):
  for log in logs[:30]:
    content = log.journal_entry or log.top_priority or "Morning/evening entry"
    render_timeline_entry("log", log.date, content, {
      "morning": "✓" if log.morning_completed else "—",
      "evening": "✓" if log.evening_completed else "—",
    })

if filter_type in ("all", "weekly"):
  with get_db() as conn:
    reviews = conn.execute("SELECT * FROM weekly_reviews ORDER BY week_start DESC LIMIT 10").fetchall()
  for review in reviews:
    try:
      output = json.loads(review["ai_output"] or "{}")
      content = output.get("week_summary", "Weekly review")
    except json.JSONDecodeError:
      content = "Weekly review"
    render_timeline_entry("weekly", date.fromisoformat(review["week_start"]), content)

if filter_type in ("all", "memory"):
  for mem in memory_repo.get_all()[:20]:
    render_timeline_entry("memory", mem.source_date or date.today(), mem.text, {"type": mem.type})

if filter_type in ("all", "coaching"):
  for resp in coach_repo.get_recent(20):
    render_timeline_entry("coaching", resp.date, resp.ai_response[:200], {"type": resp.session_type})

if not logs:
  empty_state("No history yet", "Import your journals or start your daily ritual.")
