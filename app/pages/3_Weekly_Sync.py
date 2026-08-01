"""Weekly Journal Batch Sync and Goal Reflection with Folder Image Scan."""

import os
import sys
from datetime import date, timedelta

_APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _APP_DIR not in sys.path:
  sys.path.insert(0, _APP_DIR)
import bootstrap  # noqa: F401

import streamlit as st
from PIL import Image

from components.layout import hero_card, info_card, page_header, section, stat_card
from database.repositories.goal_repository import GoalRepository
from services.local_ocr_service import extract_text_from_image
from services.weekly_sync_service import WeeklySyncService
from utils import configure_page, init_app

configure_page("Weekly Sync | GoalOS", "🔄")
init_app()

today = date.today()
week_start = today - timedelta(days=today.weekday())
week_end = week_start + timedelta(days=6)

sync_service = WeeklySyncService()
goal_repo = GoalRepository()
active_goals = goal_repo.get_active()

page_header("Weekly & Monthly Sync", "Handwritten Journal Batch Processing & Goal Alignment")

upload_tab, gallery_tab, report_tab, history_tab = st.tabs([
  "Batch Upload & Folder Scan",
  "Journal Page Gallery",
  "Weekly & Monthly Reports",
  "Sync History",
])

with upload_tab:
  section("Select Import Mode")
  import_mode = st.radio(
    "Import Source",
    ["July Journal Folder (Preset)", "Custom Local Folder Path", "CSV File Upload", "Single Image Scan"],
    horizontal=True,
  )

  if import_mode == "July Journal Folder (Preset)":
    july_folder = r"c:\Users\jegad\projects\GoalOS\data\July Journal"
    st.info(f"Preset Directory: `{july_folder}` (31 Journal `.jpg` Images)")

    if st.button("Scan & Group July Journal (31 Days → 4 Weeks + Monthly)", type="primary", use_container_width=True):
      with st.spinner("Scanning 31 daily journal pages for July 2026..."):
        raw_entries = sync_service.scan_journal_folder(july_folder, start_date=date(2026, 7, 1))
        weeks = sync_service.group_entries_into_weeks(raw_entries)
        st.session_state["july_raw_entries"] = raw_entries
        st.session_state["july_weeks"] = weeks

        # Generate reports for all weeks
        weekly_reports = []
        for week in weeks:
          rep = sync_service.generate_weekly_report(week["entries"], active_goals)
          rep["week_start"] = week["week_start"]
          rep["week_end"] = week["week_end"]
          weekly_reports.append(rep)
          # Save each week to database
          sync_service.save_sync_log(
            week_start=week["week_start"],
            week_end=week["week_end"],
            source_type="folder_scan",
            raw_content=f"July Journal Week {week['week_index']} ({len(week['entries'])} pages)",
            summary=rep["summary"],
            wins=rep["wins"],
            lessons=rep["lessons"],
            alignment_score=rep["goal_alignment_score"],
            next_week_focus=rep["next_week_focus"],
          )

        monthly_summary = sync_service.generate_monthly_summary(weekly_reports, "July 2026")
        st.session_state["july_weekly_reports"] = weekly_reports
        st.session_state["july_monthly_summary"] = monthly_summary
        st.toast("Successfully processed July 2026 Journal (4 Weeks + Monthly Summary)!", icon="🎉")

  elif import_mode == "Custom Local Folder Path":
    folder_input = st.text_input("Local Folder Path", value=r"c:\Users\jegad\projects\GoalOS\data\July Journal")
    if folder_input and st.button("Scan Custom Folder"):
      entries = sync_service.scan_journal_folder(folder_input)
      weeks = sync_service.group_entries_into_weeks(entries)
      st.session_state["custom_entries"] = entries
      st.session_state["custom_weeks"] = weeks
      st.success(f"Scanned {len(entries)} journal pages across {len(weeks)} calendar weeks.")

  elif import_mode == "CSV File Upload":
    uploaded_file = st.file_uploader("Upload Weekly Journal CSV", type=["csv"])
    if uploaded_file is not None:
      entries = sync_service.parse_csv(uploaded_file.getvalue())
      st.session_state["parsed_weekly_entries"] = entries
      st.success(f"Parsed {len(entries)} daily entries from CSV.")

  elif import_mode == "Single Image Scan":
    uploaded_image = st.file_uploader("Upload Single Page Image", type=["png", "jpg", "jpeg"])
    if uploaded_image is not None:
      ocr_res = extract_text_from_image(uploaded_image.getvalue())
      if ocr_res["success"]:
        st.text_area("Extracted Raw Text", ocr_res["text"], height=200)
      else:
        info_card(ocr_res["error"], "warning")

with gallery_tab:
  entries = st.session_state.get("july_raw_entries") or st.session_state.get("custom_entries") or []
  if not entries:
    info_card("No folder scan active yet. Click 'Scan & Group July Journal' on the Batch Upload tab.", "info")
  else:
    section(f"Journal Page Gallery ({len(entries)} Pages Scanned)")
    page_num = st.slider("Select Day Page", 1, len(entries), 1)
    selected_entry = entries[page_num - 1]

    col_img, col_details = st.columns([1, 1])
    with col_img:
      st.markdown(f"**Filename:** `{selected_entry['filename']}`")
      if os.path.exists(selected_entry["file_path"]):
        try:
          img = Image.open(selected_entry["file_path"])
          st.image(img, use_container_width=True, caption=f"Day {selected_entry['day_number']} — {selected_entry['date']}")
        except Exception:
          st.warning("Could not render image preview.")
    with col_details:
      st.markdown(f"### Day {selected_entry['day_number']} Overview")
      st.write(f"**Date:** {selected_entry['date']}")
      st.write(f"**Gratitude / Focus:** {selected_entry['gratitude']}")
      st.write(f"**Reflection:** {selected_entry['review']}")
      st.write(f"**Takeaway:** {selected_entry['takeaway']}")

with report_tab:
  monthly_summary = st.session_state.get("july_monthly_summary")
  weekly_reports = st.session_state.get("july_weekly_reports")

  if monthly_summary and weekly_reports:
    section(f"📅 {monthly_summary['month']} Monthly Overview")

    c1, c2, c3 = st.columns(3)
    with c1:
      stat_card("Total Days Logged", f"{monthly_summary['total_days_logged']} / 31")
    with c2:
      stat_card("Avg Goal Alignment", f"{monthly_summary['average_goal_alignment']}%")
    with c3:
      stat_card("Weekly Syncs Created", monthly_summary["total_weeks"])

    hero_card("Monthly Key Takeaway", monthly_summary["monthly_takeaway"])

    section("4 Weekly Sync Reports (July 2026)")
    for idx, rep in enumerate(weekly_reports):
      with st.expander(f"Week {idx + 1} ({rep['week_start']} to {rep['week_end']}) — Alignment: {rep['goal_alignment_score']}%", expanded=(idx == 0)):
        st.write(f"**Summary:**\n{rep['summary']}")
        col_w, col_l = st.columns(2)
        with col_w:
          st.markdown("**Key Wins:**")
          st.write(rep["wins"])
        with col_l:
          st.markdown("**Lessons:**")
          st.write(rep["lessons"])
        st.markdown(f"**Next Week Focus:**\n{rep['next_week_focus']}")
  else:
    info_card("No weekly/monthly reports generated yet. Run the July Journal Scan on the Batch Upload tab.", "info")

with history_tab:
  section("Historical Weekly Sync Logs")
  logs = sync_service.get_recent_sync_logs(15)
  if logs:
    for log in logs:
      with st.expander(f"Week of {log['week_start']} (Alignment: {log['goal_alignment_score']}%)"):
        st.write(f"**Source:** {log['source_type'].upper()}")
        st.write(f"**Summary:**\n{log['summary']}")
        st.write(f"**Next Week Focus:**\n{log['next_week_focus']}")
  else:
    info_card("No previous weekly sync logs stored.", "default")
