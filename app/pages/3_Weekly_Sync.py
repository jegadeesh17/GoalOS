"""Weekly Journal Batch Sync and Goal Reflection with Folder Image Scan."""

import calendar
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

# Journal folder lives at data/Journal — reused every month
JOURNAL_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "Journal"))

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


def _detect_month_from_folder(folder_path: str) -> tuple[str, date]:
  """Count images and guess the month start date. Defaults to previous month."""
  valid_exts = (".jpg", ".jpeg", ".png")
  if os.path.isdir(folder_path):
    count = len([f for f in os.listdir(folder_path) if f.lower().endswith(valid_exts)])
  else:
    count = 0

  # Default to the previous month (most common use case: syncing last month's journal)
  prev_month_end = today.replace(day=1) - timedelta(days=1)
  month_start = prev_month_end.replace(day=1)
  month_name = month_start.strftime("%B %Y")
  days_in_month = calendar.monthrange(month_start.year, month_start.month)[1]
  return month_name, month_start, days_in_month, count


with upload_tab:
  section("Select Import Mode")
  import_mode = st.radio(
    "Import Source",
    ["Journal Folder (Preset)", "Custom Local Folder Path", "CSV File Upload", "Single Image Scan"],
    horizontal=True,
  )

  if import_mode == "Journal Folder (Preset)":
    month_name, month_start, days_in_month, image_count = _detect_month_from_folder(JOURNAL_FOLDER)

    st.info(f"📂 Preset Directory: `{JOURNAL_FOLDER}`\n\n**Detected:** {image_count} journal images · **Assumed Month:** {month_name} (starts {month_start.isoformat()})")

    with st.expander("⚙️ Adjust Month Settings", expanded=False):
      col_m, col_d = st.columns(2)
      with col_m:
        override_start = st.date_input("Month Start Date", value=month_start)
      with col_d:
        override_month_name = st.text_input("Month Label", value=month_name)
      if override_start:
        month_start = override_start
        month_name = override_month_name or month_start.strftime("%B %Y")
        days_in_month = calendar.monthrange(month_start.year, month_start.month)[1]

    if st.button(f"Scan & Group Journal ({image_count} Pages → Weekly + Monthly)", type="primary", use_container_width=True):
      with st.spinner(f"Scanning {image_count} daily journal pages for {month_name}..."):
        raw_entries = sync_service.scan_journal_folder(JOURNAL_FOLDER, start_date=month_start)
        weeks = sync_service.group_entries_into_weeks(raw_entries)
        st.session_state["scan_raw_entries"] = raw_entries
        st.session_state["scan_weeks"] = weeks

        weekly_reports = []
        for week in weeks:
          rep = sync_service.generate_weekly_report(week["entries"], active_goals)
          rep["week_start"] = week["week_start"]
          rep["week_end"] = week["week_end"]
          weekly_reports.append(rep)
          sync_service.save_sync_log(
            week_start=week["week_start"],
            week_end=week["week_end"],
            source_type="folder_scan",
            raw_content=f"{month_name} Week {week['week_index']} ({len(week['entries'])} pages)",
            summary=rep["summary"],
            wins=rep["wins"],
            lessons=rep["lessons"],
            alignment_score=rep["goal_alignment_score"],
            next_week_focus=rep["next_week_focus"],
          )

        monthly_summary = sync_service.generate_monthly_summary(weekly_reports, month_name)
        st.session_state["scan_weekly_reports"] = weekly_reports
        st.session_state["scan_monthly_summary"] = monthly_summary
        st.toast(f"Processed {month_name} Journal ({len(weeks)} Weeks + Monthly Summary)!", icon="🎉")

  elif import_mode == "Custom Local Folder Path":
    folder_input = st.text_input("Local Folder Path", value=JOURNAL_FOLDER)
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
  entries = st.session_state.get("scan_raw_entries") or st.session_state.get("custom_entries") or []
  if not entries:
    info_card("No folder scan active yet. Run a scan from the Batch Upload tab.", "info")
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
  monthly_summary = st.session_state.get("scan_monthly_summary")
  weekly_reports = st.session_state.get("scan_weekly_reports")

  if monthly_summary and weekly_reports:
    section(f"📅 {monthly_summary['month']} Monthly Review & Cascading Goal Impact")

    c1, c2, c3 = st.columns(3)
    with c1:
      stat_card("Total Days Logged", f"{monthly_summary['total_days_logged']}")
    with c2:
      stat_card("Avg Goal Alignment", f"{monthly_summary['average_goal_alignment']}%")
    with c3:
      stat_card("Weekly Syncs", f"{monthly_summary['total_weeks']}")

    hero_card("Monthly Key Takeaway", monthly_summary["monthly_takeaway"])

    if "cascading_goal_impact" in monthly_summary:
      info_card(f"🎯 **Cascading Goal Impact (1-Month ➔ 1-Year ➔ 5-Year):**\n\n{monthly_summary['cascading_goal_impact']}", "info")

    section(f"Weekly Sync Reports ({monthly_summary['month']})")
    for idx, rep in enumerate(weekly_reports):
      with st.expander(f"Week {idx + 1} ({rep.get('week_start', '')} to {rep.get('week_end', '')}) — Alignment: {rep.get('goal_alignment_score', 0.0)}%", expanded=(idx == 0)):
        if "urgent_coaching_takeaway" in rep:
          st.error(f"⚡ **Urgent Weekly Takeaway:** {rep['urgent_coaching_takeaway']}")
        
        st.markdown(f"**Weekly Summary:**\n{rep['summary']}")
        
        if "task_goal_mapping" in rep:
          st.markdown(f"**Task ➔ Goal Mapping:**\n{rep['task_goal_mapping']}")

        col_w, col_l = st.columns(2)
        with col_w:
          st.markdown("**Key Reflections / Wins:**")
          st.write(rep.get("wins", "N/A"))
        with col_l:
          st.markdown("**Takeaways:**")
          st.write(rep.get("takeaways", rep.get("lessons", "N/A")))
  else:
    info_card("No weekly/monthly reports generated yet. Run a folder scan on the Batch Upload tab.", "info")

with history_tab:
  section("Historical Weekly Sync Logs")
  logs = sync_service.get_recent_sync_logs(15)
  if logs:
    for log in logs:
      with st.expander(f"Week of {log['week_start']} (Alignment: {log['goal_alignment_score']}%)"):
        st.write(f"**Source:** {log['source_type'].upper()}")
        st.write(f"**Summary:**\n{log['summary']}")
        st.write(f"**Next Week Focus:**\n{log.get('next_week_focus', 'N/A')}")
  else:
    info_card("No previous weekly sync logs stored.", "default")
