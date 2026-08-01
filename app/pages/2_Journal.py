"""Journal Import & Daily Log Page with Image Scan Options."""

import calendar
import json
import os
import sys
import uuid
from datetime import date, timedelta

_APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _APP_DIR not in sys.path:
  sys.path.insert(0, _APP_DIR)
import bootstrap  # noqa: F401
import streamlit as st
from PIL import Image

from components.layout import hero_card, info_card, mentor_panel, page_header, section
from database.repositories.goal_repository import GoalRepository
from database.repositories.log_repository import LogRepository
from database.repositories.milestone_repository import MilestoneRepository
from models.daily_log import DailyLogUpdate
from services.journal_helpers import (
  ensure_task_ids,
  load_tasks_from_log,
  log_task_stats,
  normalize_tasks,
  pack_tasks,
  serialize_journal_fields,
)
from services.local_ocr_service import extract_text_from_image
from services.weekly_sync_service import WeeklySyncService
from utils import configure_page, get_coach_service, init_app

configure_page("Journal | GoalOS", "📓")
init_app()

today = date.today()
JOURNAL_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "Journal"))

log_repo, goal_repo = LogRepository(), GoalRepository()
sync_service = WeeklySyncService()
coach = get_coach_service()

page_header("Journal & Page Import", "Upload Handwritten Journal Images or Log Daily Intentions")

mode_tab, gallery_tab, digital_tab = st.tabs([
  "📷 Import Journal Images (2 Options)",
  "🖼️ Scanned Journal Gallery",
  "📝 Digital Daily Log (Optional)",
])

with mode_tab:
  section("Select Image Upload Method")
  upload_option = st.radio(
    "Upload Mode",
    ["Option 1: Batch Folder Scan (Preset data/Journal)", "Option 2: Upload Files Directly (Single Image / CSV)"],
    horizontal=True,
  )

  if "Option 1" in upload_option:
    st.info(f"📂 **Preset Directory:** `{JOURNAL_FOLDER}`\n\nScans all `.jpg` / `.png` handwritten journal images from your local folder into SQLite daily logs.")

    if os.path.exists(JOURNAL_FOLDER):
      files = [f for f in os.listdir(JOURNAL_FOLDER) if f.lower().endswith((".jpg", ".png", ".jpeg"))]
      st.caption(f"Detected {len(files)} journal page images in `{JOURNAL_FOLDER}`.")

      if st.button("Scan Preset Folder Images → Save to Database", type="primary", use_container_width=True):
        with st.spinner(f"Running OCR on {len(files)} journal pages..."):
          entries = sync_service.scan_journal_folder(JOURNAL_FOLDER, start_date=today.replace(day=1))
          st.session_state["scanned_entries"] = entries
          st.success(f"Successfully processed {len(entries)} journal pages into database!")
          st.toast(f"Imported {len(entries)} pages!", icon="🎉")
    else:
      st.error(f"Folder not found: {JOURNAL_FOLDER}")

  else:
    col_img, col_csv = st.columns(2)
    with col_img:
      section("Upload Single Journal Image")
      img_file = st.file_uploader("Choose Journal Page Image", type=["jpg", "jpeg", "png"])
      if img_file is not None:
        st.image(Image.open(img_file), caption="Uploaded Page", use_container_width=True)
        if st.button("OCR Scan Uploaded Image"):
          with st.spinner("Extracting text..."):
            ocr_res = extract_text_from_image(img_file.getvalue())
            if ocr_res.get("success"):
              st.success("Extracted Text:")
              st.text_area("OCR Text Output", ocr_res.get("text", ""), height=150)
            else:
              st.error(ocr_res.get("error", "OCR failed"))

    with col_csv:
      section("Upload CSV Journal File")
      csv_file = st.file_uploader("Choose Journal CSV File", type=["csv"])
      if csv_file is not None:
        if st.button("Parse CSV Entries"):
          entries = sync_service.parse_csv(csv_file.getvalue())
          st.session_state["parsed_csv_entries"] = entries
          st.success(f"Parsed {len(entries)} entries from CSV file!")

with gallery_tab:
  entries = st.session_state.get("scanned_entries") or []
  if not entries:
    info_card("No folder scan active yet. Click 'Scan Preset Folder Images' on the import tab.", "info")
  else:
    section(f"Journal Page Gallery ({len(entries)} Pages Scanned)")
    page_num = st.slider("Select Page Number", 1, len(entries), 1)
    selected_entry = entries[page_num - 1]

    col_i, col_d = st.columns([1, 1])
    with col_i:
      st.markdown(f"**Filename:** `{selected_entry['filename']}`")
      img_path = selected_entry.get("file_path") or os.path.join(JOURNAL_FOLDER, selected_entry["filename"])
      if os.path.exists(img_path):
        try:
          st.image(Image.open(img_path), use_container_width=True, caption=f"Day {selected_entry['day_number']} — {selected_entry['date']}")
        except Exception:
          st.warning("Could not render image preview.")
    with col_d:
      st.markdown(f"### Day {selected_entry['day_number']} Overview")
      st.write(f"**Date:** {selected_entry['date']}")
      st.write(f"**Gratitude / Focus:** {selected_entry['gratitude']}")
      st.write(f"**Reflection:** {selected_entry['review']}")
      st.write(f"**Takeaway:** {selected_entry['takeaway']}")

with digital_tab:
  section("Digital Morning & Evening Log")
  existing = log_repo.get_by_date(today)
  gratitude = st.text_input("Morning Focus / Gratitude", value=existing.gratitude if existing else "")
  journal_text = st.text_area("Evening Journal Reflection", value=existing.journal_entry if existing else "", height=100)
  takeaway = st.text_input("One Lesson / Takeaway", value=existing.takeaway if existing else "")

  if st.button("Save Digital Entry", type="primary"):
    log_repo.upsert_fields(today, DailyLogUpdate(gratitude=gratitude, journal_entry=journal_text, takeaway=takeaway, morning_completed=True, evening_completed=True))
    st.toast("Saved digital entry!", icon="✅")
