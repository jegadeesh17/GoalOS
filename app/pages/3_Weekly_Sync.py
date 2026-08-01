"""Weekly Journal Batch Sync and Goal Reflection."""

import os
import sys
from datetime import date, timedelta

_APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _APP_DIR not in sys.path:
  sys.path.insert(0, _APP_DIR)
import bootstrap  # noqa: F401

import streamlit as st

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

page_header("Weekly Sync", f"Week of {week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}")

upload_tab, review_tab, history_tab = st.tabs(["Batch Upload", "Weekly Report & Focus", "Sync History"])

with upload_tab:
  section("Upload Weekly Handwritten Journal")
  st.caption("Upload your weekly handwritten journal data as a CSV file or scan page images using local offline OCR (zero external API calls).")

  col_left, col_right = st.columns([2, 1])

  with col_left:
    file_type = st.radio("Import Type", ["CSV File (Recommended)", "Image Scan (Local OCR)"], horizontal=True)

    if file_type == "CSV File (Recommended)":
      uploaded_file = st.file_uploader("Upload Weekly Journal CSV", type=["csv"])
      if uploaded_file is not None:
        content = uploaded_file.getvalue()
        entries = sync_service.parse_csv(content)
        st.session_state["parsed_weekly_entries"] = entries
        st.success(f"Parsed {len(entries)} daily entries from CSV.")

    else:
      uploaded_image = st.file_uploader("Upload Journal Page Image", type=["png", "jpg", "jpeg"])
      if uploaded_image is not None:
        img_bytes = uploaded_image.getvalue()
        with st.spinner("Extracting text locally via Tesseract OCR..."):
          ocr_result = extract_text_from_image(img_bytes)

        if ocr_result["success"]:
          st.text_area("Extracted Raw Text", ocr_result["text"], height=200)
          st.session_state["raw_ocr_text"] = ocr_result["text"]
          # Create single entry fallback
          st.session_state["parsed_weekly_entries"] = [{
            "date": today.isoformat(),
            "gratitude": "",
            "tasks": "",
            "wins": "",
            "review": ocr_result["text"],
            "takeaway": "",
          }]
        else:
          info_card(ocr_result["error"], "warning")

  with col_right:
    section("CSV Format Helper")
    st.markdown("""
    **Expected CSV Headers:**
    `date`, `gratitude`, `tasks`, `wins`, `review`, `takeaway`

    **Sample Row:**
    `2026-07-28`, `Quiet morning`, `Build feature`, `Finished API`, `Felt focused`, `Plan before code`
    """)

    sample_csv = """date,gratitude,tasks,wins,review,takeaway
2026-07-27,Quiet morning,Study SQL,Finished review,Productive block,Schedule exercise early
2026-07-28,Good sleep,Build portfolio,Completed demo,High focus,Protect morning hours
"""
    st.download_button(
      "Download Sample CSV Template",
      data=sample_csv,
      file_name="weekly_journal_template.csv",
      mime="text/csv",
      use_container_width=True,
    )

with review_tab:
  entries = st.session_state.get("parsed_weekly_entries", [])
  if not entries:
    info_card("No weekly journal entries uploaded yet. Upload a CSV on the Batch Upload tab to generate your report.", "info")
  else:
    section("Parsed Journal Entries")
    st.dataframe(entries, use_container_width=True)

    if st.button("Generate Weekly Synthesis & Goal Alignment Report", type="primary", use_container_width=True):
      report = sync_service.generate_weekly_report(entries, active_goals)
      st.session_state["last_weekly_report"] = report

      # Save to database
      sync_service.save_sync_log(
        week_start=week_start,
        week_end=week_end,
        source_type="csv" if file_type.startswith("CSV") else "ocr_image",
        raw_content=str(entries),
        summary=report["summary"],
        wins=report["wins"],
        lessons=report["lessons"],
        alignment_score=report["goal_alignment_score"],
        next_week_focus=report["next_week_focus"],
      )
      st.toast("Weekly Sync Report saved!", icon="✅")

  report = st.session_state.get("last_weekly_report")
  if report:
    section("Weekly Synthesis & Goal Alignment")

    c1, c2, c3 = st.columns(3)
    with c1:
      stat_card("Days Logged", f"{report['total_days_logged']} days")
    with c2:
      stat_card("Goal Alignment", f"{report['goal_alignment_score']}%")
    with c3:
      stat_card("Active Goals Linked", report["active_goals_count"])

    st.markdown("### Summary")
    st.info(report["summary"])

    col1, col2 = st.columns(2)
    with col1:
      st.markdown("### 🏆 Key Wins")
      st.write(report["wins"])
    with col2:
      st.markdown("### 💡 Key Lessons")
      st.write(report["lessons"])

    section("🎯 Next Week Focus Areas")
    hero_card("Priority Focus Items", report["next_week_focus"])

with history_tab:
  section("Previous Weekly Sync Logs")
  logs = sync_service.get_recent_sync_logs(10)
  if logs:
    for log in logs:
      with st.expander(f"Week of {log['week_start']} (Alignment: {log['goal_alignment_score']}%)"):
        st.write(f"**Source:** {log['source_type'].upper()}")
        st.write(f"**Summary:**\n{log['summary']}")
        st.write(f"**Next Week Focus:**\n{log['next_week_focus']}")
  else:
    info_card("No previous weekly sync logs stored.", "default")
