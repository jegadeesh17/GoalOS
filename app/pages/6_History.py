"""History page with import and semantic search."""

import os
import sys

_APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _APP_DIR not in sys.path:
  sys.path.insert(0, _APP_DIR)
import json
import tempfile
from datetime import date
from pathlib import Path

import bootstrap  # noqa: F401
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

page_header("History", "Past Journals, Vector Memory Search, and Log History")

log_repo = LogRepository()
memory_repo = MemoryRepository()
coach_repo = CoachRepository()
memory_service = MemoryService()
import_service = JournalImportService()

c1, c2, c3 = st.columns(3)
with c1:
  stat_card("Daily Logs", log_repo.count())
with c2:
  stat_card("Memories", memory_repo.count())
with c3:
  stat_card("Coach Sessions", coach_repo.count())

section("Semantic Search & Memories")
col1, col2, col3 = st.columns([3, 1, 1])
search_query = col1.text_input("Semantic search", placeholder="Search memories and journals...", label_visibility="collapsed")
filter_type = col2.selectbox("Filter", ["all", "log", "memory", "coaching"], label_visibility="collapsed")
memory_status = col3.selectbox("Memory status", ["active", "completed", "archived", "all"], label_visibility="collapsed")

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

if filter_type in ("all", "coaching"):
  for resp in coach_repo.get_recent(20):
    render_timeline_entry("coaching", resp.date, resp.ai_response[:200], {"type": resp.session_type})

if not logs:
  empty_state("No history yet", "Import your journals or start logging.")
