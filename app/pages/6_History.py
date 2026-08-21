"""History page displaying historical daily journal records matching the exact journal format."""

import os
import sys

_APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _APP_DIR not in sys.path:
  sys.path.insert(0, _APP_DIR)

import bootstrap  # noqa: F401
import pandas as pd
import streamlit as st

from components.layout import empty_state, page_header, section, stat_card
from database.connection import get_db
from database.repositories.coach_repository import CoachRepository
from database.repositories.log_repository import LogRepository
from database.repositories.memory_repository import MemoryRepository
from utils import configure_page, init_app

configure_page("History | GoalOS", "📜")
init_app()

page_header("History", "Tabular Journal Records & Daily Log History")

log_repo = LogRepository()
memory_repo = MemoryRepository()
coach_repo = CoachRepository()

# Query raw relational database records
with get_db() as conn:
  cursor = conn.execute("SELECT * FROM daily_logs ORDER BY date DESC")
  column_names = [col[0] for col in cursor.description]
  raw_rows = cursor.fetchall()
  records = [dict(zip(column_names, row, strict=False)) for row in raw_rows]

if not records:
  empty_state("No history records found", "Import or log daily journals to view historical records.")
else:
  df_all = pd.DataFrame(records)

  # Calculate summary metrics
  total_logs = len(df_all)
  rates = [float(r) for r in df_all["task_completion_rate"].dropna() if pd.notna(r) and r != ""]
  avg_rate = round(sum(rates) / len(rates), 1) if rates else 0.0
  latest_date = df_all["date"].iloc[0] if not df_all.empty else "N/A"
  total_memories = memory_repo.count()

  # Summary statistics
  c1, c2, c3, c4 = st.columns(4)
  with c1:
    stat_card("Total Journal Entries", total_logs)
  with c2:
    stat_card("Avg Task Completion", f"{avg_rate}%")
  with c3:
    stat_card("Latest Entry", latest_date)
  with c4:
    stat_card("Saved Memories", total_memories)

  # Fill nulls and normalize fields
  df = df_all.copy()
  boolean_cols = ["morning_completed", "evening_completed", "workout_completed", "imported"]
  for col in boolean_cols:
    if col in df.columns:
      df[col] = df[col].apply(lambda v: bool(v) if pd.notna(v) and v is not None else False)

  text_cols = [
    "top_priority", "supporting_task_1", "supporting_task_2", "gratitude",
    "intention", "anxiety", "anticipation", "free_write", "calendar_constraints",
    "time_blocks", "planned_tasks", "journal_entry", "tasks_completed",
    "workout_notes", "biggest_distraction", "one_win", "one_lesson", "takeaway",
    "morning_ai_output", "evening_ai_output", "import_source",
  ]
  for col in text_cols:
    if col in df.columns:
      df[col] = df[col].fillna("").astype(str)

  # Search & Filtering Controls
  section("Search & Filter")
  f_col1, f_col2, f_col3 = st.columns([2, 1, 1])

  with f_col1:
    search_query = st.text_input(
      "Search logs",
      placeholder="Search across date, gratitude, plan, tasks, review, takeaway...",
      label_visibility="collapsed",
    )

  with f_col2:
    months_list = ["All Months"] + sorted(list(set(df["date"].str[:7])), reverse=True)
    selected_month = st.selectbox("Filter by Month", months_list, index=0, label_visibility="collapsed")

  with f_col3:
    view_mode = st.selectbox("Table View", ["Journal View (Customized)", "Full Database Schema (38 Cols)"], index=0, label_visibility="collapsed")

  # Apply month filter
  filtered_df = df.copy()
  if selected_month != "All Months":
    filtered_df = filtered_df[filtered_df["date"].str.startswith(selected_month)]

  # Apply search query
  if search_query.strip():
    term = search_query.strip().lower()
    searchable_cols = [c for c in text_cols + ["date", "id"] if c in filtered_df.columns]
    mask = filtered_df[searchable_cols].astype(str).apply(
      lambda row: row.str.lower().str.contains(term, regex=False)
    ).any(axis=1)
    filtered_df = filtered_df[mask]

  section(f"Journal Records ({len(filtered_df)} entries)")

  if "Journal View" in view_mode:
    # Prepare clean Journal View with exact pillars
    journal_cols = [
      "date",
      "gratitude",
      "time_blocks",
      "top_priority",
      "tasks_completed",
      "task_completion_rate",
      "journal_entry",
      "takeaway",
      "import_source",
    ]
    # Ensure all exist
    display_df = filtered_df[[c for c in journal_cols if c in filtered_df.columns]].copy()

    # Column configuration optimized for readability
    journal_column_config = {
      "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD", width="small"),
      "gratitude": st.column_config.TextColumn("Morning Gratitude", width="large"),
      "time_blocks": st.column_config.TextColumn("Plan / Schedule", width="large"),
      "top_priority": st.column_config.TextColumn("Top Priority (P1)", width="medium"),
      "tasks_completed": st.column_config.TextColumn("Tasks & Status", width="large"),
      "task_completion_rate": st.column_config.ProgressColumn(
        "Completion %",
        min_value=0.0,
        max_value=100.0,
        format="%.1f%%",
        width="small",
      ),
      "journal_entry": st.column_config.TextColumn("Evening Review / Reflection", width="large"),
      "takeaway": st.column_config.TextColumn("Takeaway / Lesson", width="large"),
      "import_source": st.column_config.TextColumn("Source", width="small"),
    }

    st.dataframe(
      display_df,
      column_config=journal_column_config,
      hide_index=True,
      use_container_width=True,
      height=560,
    )

  else:
    # Full Relational Database Columns
    column_config = {
      "id": st.column_config.NumberColumn("id", width="small"),
      "date": st.column_config.DateColumn("date", format="YYYY-MM-DD", width="medium"),
      "morning_completed": st.column_config.CheckboxColumn("morning_completed", width="small"),
      "sleep_hours": st.column_config.NumberColumn("sleep_hours", format="%.1f", width="small"),
      "sleep_quality": st.column_config.NumberColumn("sleep_quality", width="small"),
      "energy_level": st.column_config.NumberColumn("energy_level", width="small"),
      "mood_morning": st.column_config.NumberColumn("mood_morning", width="small"),
      "expected_focus": st.column_config.NumberColumn("expected_focus", width="small"),
      "available_hours": st.column_config.NumberColumn("available_hours", format="%.1f", width="small"),
      "calendar_constraints": st.column_config.TextColumn("calendar_constraints", width="medium"),
      "free_write": st.column_config.TextColumn("free_write", width="large"),
      "intention": st.column_config.TextColumn("intention", width="medium"),
      "anxiety": st.column_config.TextColumn("anxiety", width="medium"),
      "anticipation": st.column_config.TextColumn("anticipation", width="medium"),
      "top_priority": st.column_config.TextColumn("top_priority", width="large"),
      "supporting_task_1": st.column_config.TextColumn("supporting_task_1", width="medium"),
      "supporting_task_2": st.column_config.TextColumn("supporting_task_2", width="medium"),
      "gratitude": st.column_config.TextColumn("gratitude", width="large"),
      "time_blocks": st.column_config.TextColumn("time_blocks", width="medium"),
      "planned_tasks": st.column_config.TextColumn("planned_tasks", width="large"),
      "evening_completed": st.column_config.CheckboxColumn("evening_completed", width="small"),
      "journal_entry": st.column_config.TextColumn("journal_entry", width="large"),
      "tasks_completed": st.column_config.TextColumn("tasks_completed", width="large"),
      "task_completion_rate": st.column_config.ProgressColumn("task_completion_rate", min_value=0.0, max_value=100.0, format="%.1f%%", width="small"),
      "deep_work_hours": st.column_config.NumberColumn("deep_work_hours", format="%.1f", width="small"),
      "workout_completed": st.column_config.CheckboxColumn("workout_completed", width="small"),
      "workout_notes": st.column_config.TextColumn("workout_notes", width="medium"),
      "biggest_distraction": st.column_config.TextColumn("biggest_distraction", width="medium"),
      "mood_evening": st.column_config.NumberColumn("mood_evening", width="small"),
      "one_win": st.column_config.TextColumn("one_win", width="large"),
      "one_lesson": st.column_config.TextColumn("one_lesson", width="large"),
      "takeaway": st.column_config.TextColumn("takeaway", width="large"),
      "morning_ai_output": st.column_config.TextColumn("morning_ai_output", width="large"),
      "evening_ai_output": st.column_config.TextColumn("evening_ai_output", width="large"),
      "imported": st.column_config.CheckboxColumn("imported", width="small"),
      "import_source": st.column_config.TextColumn("import_source", width="small"),
      "created_at": st.column_config.TextColumn("created_at", width="medium"),
      "updated_at": st.column_config.TextColumn("updated_at", width="medium"),
    }

    st.dataframe(
      filtered_df,
      column_config=column_config,
      hide_index=True,
      use_container_width=True,
      height=560,
    )

  # Detailed Record Inspector Card
  section("Full Entry Inspector")
  all_dates = [str(d) for d in filtered_df["date"].tolist()]
  if all_dates:
    selected_date = st.selectbox("Select entry date to inspect full journal details", all_dates, index=0)

    if selected_date:
      selected_row = filtered_df[filtered_df["date"] == selected_date]
      if not selected_row.empty:
        r = selected_row.iloc[0]
        with st.container(border=True):
          header_col, rate_col = st.columns([3, 1])
          with header_col:
            st.markdown(f"### 📅 Journal Entry: `{r['date']}`")
            st.caption(f"Source: `{r['import_source'] or 'manual'}` · Updated: `{r['updated_at']}`")
          with rate_col:
            rate_val = r["task_completion_rate"]
            if pd.notna(rate_val) and rate_val != "":
              st.metric("Task Completion Rate", f"{float(rate_val):.1f}%")

          c_left, c_right = st.columns(2)
          with c_left:
            st.markdown("#### 🌅 Morning Pillar")
            if r["gratitude"]:
              st.markdown(f"**🙏 Morning Gratitude / Focus:**\n> *\"{r['gratitude']}\"*")
            if r["top_priority"]:
              st.markdown(f"**🎯 Top Priority (P1):** `{r['top_priority']}`")
            if r["time_blocks"]:
              st.markdown("**⏰ Time-Blocked Schedule / Plan:**")
              st.code(r["time_blocks"], language="text")

          with c_right:
            st.markdown("#### 🌙 Evening Pillar")
            if r["journal_entry"]:
              st.markdown(f"**📖 Evening Reflection / Review:**\n> *\"{r['journal_entry']}\"*")
            if r["takeaway"] or r["one_lesson"]:
              st.markdown(f"**💡 Key Takeaway / Lesson:**\n> *\"{r['takeaway'] or r['one_lesson']}\"*")
            if r["tasks_completed"]:
              st.markdown("**✅ Tasks & Execution:**")
              for t_line in r["tasks_completed"].split("\n"):
                if t_line.strip():
                  if "(tick)" in t_line.lower() or "✓" in t_line or "✔" in t_line or " X" in t_line:
                    st.markdown(f"- ✅ **{t_line.strip()}**")
                  else:
                    st.markdown(f"- ⏳ {t_line.strip()}")
