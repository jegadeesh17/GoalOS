"""Today's Journal — morning plans + evening review in your handwritten style."""

import json
from datetime import date

import streamlit as st

from components.layout import coaching_block, hero_card, info_card, page_header, section
from database.repositories.log_repository import LogRepository
from models.daily_log import DailyLogCreate
from services.journal_helpers import (
  load_tasks_from_log,
  log_task_stats,
  normalize_tasks,
  pack_tasks,
  serialize_journal_fields,
)
from utils import configure_page, get_coach_service, init_app

configure_page("Today's Journal | GoalOS", "📓")
init_app()

today = date.today()
log_repo = LogRepository()
coach = get_coach_service()
existing = log_repo.get_by_date(today)
task_state_key = f"tasks_{today.isoformat()}"


def _plans_text(log) -> str:
  if not log or not log.time_blocks:
    return ""
  try:
    blocks = json.loads(log.time_blocks)
    if isinstance(blocks, list) and blocks and isinstance(blocks[0], dict) and "start" in blocks[0]:
      return "\n".join(f"{b['start']} - {b['end']}: {b['activity']}" for b in blocks)
    return str(log.time_blocks)
  except (json.JSONDecodeError, TypeError):
    return log.time_blocks or ""


def _init_task_state() -> list[dict]:
  if task_state_key not in st.session_state:
    loaded = load_tasks_from_log(existing)
    st.session_state[task_state_key] = loaded or []
  return st.session_state[task_state_key]


def _render_task_editor() -> list[dict]:
  """Add-entry task list — #1 is highest priority."""
  tasks = _init_task_state()
  section("TASKS")
  st.caption("#1 is your highest priority. Add tasks in order of importance.")

  if not tasks:
    st.caption("No tasks yet — add your first one below.")

  remove_idx = None
  move = None
  for i, task in enumerate(tasks):
    col_rank, col_text, col_up, col_down, col_del = st.columns([0.6, 7, 0.5, 0.5, 0.5])
    with col_rank:
      st.markdown(f"**#{i + 1}**")
    with col_text:
      tasks[i]["text"] = st.text_input(
        f"Task {i + 1}",
        value=task.get("text", ""),
        key=f"m_task_{today}_{i}",
        label_visibility="collapsed",
        placeholder="e.g. Solve 10 Codekata problems",
      )
    with col_up:
      if i > 0 and st.button("↑", key=f"m_up_{today}_{i}", help="Higher priority"):
        move = (i, i - 1)
    with col_down:
      if i < len(tasks) - 1 and st.button("↓", key=f"m_down_{today}_{i}", help="Lower priority"):
        move = (i, i + 1)
    with col_del:
      if st.button("✕", key=f"m_del_{today}_{i}", help="Remove"):
        remove_idx = i

  if move:
    a, b = move
    tasks[a], tasks[b] = tasks[b], tasks[a]
    st.session_state[task_state_key] = normalize_tasks(tasks)
    st.rerun()

  if remove_idx is not None:
    tasks.pop(remove_idx)
    st.session_state[task_state_key] = normalize_tasks(tasks)
    st.rerun()

  if st.button("+ Add task", use_container_width=False):
    tasks.append({"text": "", "completed": False, "priority": len(tasks) + 1})
    st.session_state[task_state_key] = tasks
    st.rerun()

  return normalize_tasks([t for t in tasks if t.get("text", "").strip()])


def _render_task_checklist(tasks: list[dict]) -> list[dict]:
  """Evening checklist — one checkbox per task."""
  section("TASKS")
  if not tasks:
    st.caption("No tasks from this morning.")
    return []

  updated = []
  done = 0
  for task in tasks:
    checked = st.checkbox(
      f"#{task['priority']}  {task['text']}",
      value=task.get("completed", False),
      key=f"e_task_{today}_{task['priority']}",
    )
    updated.append({**task, "completed": checked})
    if checked:
      done += 1

  st.caption(f"{done}/{len(updated)} completed")
  return updated


plans_default = _plans_text(existing)

page_header("Today's Journal", today.strftime("%A, %d %B %Y"))

tab_morning, tab_evening = st.tabs(["Morning", "Evening"])

# ── Morning ──────────────────────────────────────────────────────────────────
with tab_morning:
  st.caption("GRATITUDE · TASKS · SLEEP & MOOD")

  gratitude = st.text_input(
    "GRATITUDE",
    value=existing.gratitude if existing else "",
    placeholder="grateful for such friendly parents.",
  )

  col1, col2, col3 = st.columns(3)
  with col1:
    sleep_hours = st.number_input(
      "Sleep (hours)",
      0.0, 12.0,
      existing.sleep_hours if existing and existing.sleep_hours else 7.0,
      0.5,
    )
  with col2:
    sleep_quality = st.slider(
      "Sleep quality",
      1, 5,
      existing.sleep_quality if existing and existing.sleep_quality else 3,
    )
  with col3:
    mood_morning = st.slider(
      "Mood",
      1, 5,
      existing.mood_morning if existing and existing.mood_morning else 3,
    )

  morning_tasks = _render_task_editor()

  with st.expander("Time slots (optional)", expanded=False):
    st.caption("Pin tasks to time — write manually if you want a schedule.")
    plans_text = st.text_area(
      "Plans",
      value=plans_default,
      height=100,
      label_visibility="collapsed",
      placeholder="10:30-12  Codekata\n2-4      Quandao project",
    )

  if existing and existing.morning_ai_output:
    try:
      mentor = json.loads(existing.morning_ai_output)
      if mentor.get("mentor_rule"):
        section("Today's Rule")
        hero_card("Mentor Rule", mentor["mentor_rule"])
        coaching_block("Why", mentor.get("why_this_rule", ""))
        coaching_block("Pattern called out", mentor.get("past_mistake_called_out", ""))
        coaching_block("If you ignore this", mentor.get("if_you_ignore_this", ""))
    except json.JSONDecodeError:
      pass

  if st.button("Save Morning & Get Mentor Rule", type="primary", use_container_width=True):
    if not morning_tasks:
      st.error("Add at least one task.")
    else:
      fields = serialize_journal_fields(gratitude, plans_text, morning_tasks)
      data = DailyLogCreate(
        date=today,
        gratitude=fields["gratitude"],
        time_blocks=fields["time_blocks"],
        planned_tasks=fields["planned_tasks"],
        tasks_completed=fields["tasks_completed"],
        task_completion_rate=fields["task_completion_rate"],
        sleep_hours=sleep_hours,
        sleep_quality=sleep_quality,
        mood_morning=mood_morning,
        morning_completed=True,
        evening_completed=existing.evening_completed if existing else False,
        journal_entry=existing.journal_entry if existing else None,
        takeaway=existing.takeaway if existing else None,
      )
      log = log_repo.upsert_by_date(data)
      with st.spinner("Mentor is reviewing your past..."):
        try:
          coach.get_morning_coaching(today, log)
          st.session_state.pop(task_state_key, None)
          st.toast("Morning saved. Today's rule is set.", icon="✅")
          st.rerun()
        except Exception as e:
          st.error(f"Mentor rule failed: {e}. Your entry was saved.")

# ── Evening ──────────────────────────────────────────────────────────────────
with tab_evening:
  st.caption("Check off tasks · REVIEW · TAKEAWAY")

  if not existing or not existing.morning_completed:
    info_card("Complete your morning journal first — tasks unlock the evening review.", "warning")
  else:
    evening_tasks = _render_task_checklist(load_tasks_from_log(existing))

    section("REVIEW")
    review = st.text_area(
      "Review",
      value=existing.journal_entry if existing else "",
      height=120,
      label_visibility="collapsed",
      placeholder="I did great work but not focusing on what matters",
    )

    section("TAKEAWAY")
    takeaway = st.text_input(
      "Takeaway",
      value=existing.takeaway if existing else "",
      placeholder="Focus and lock in.",
    )

    if st.button("Close the Day", type="primary", use_container_width=True):
      packed = pack_tasks(evening_tasks)
      data = DailyLogCreate(
        date=today,
        gratitude=existing.gratitude,
        time_blocks=existing.time_blocks,
        planned_tasks=packed["planned_tasks"],
        tasks_completed=packed["tasks_completed"],
        task_completion_rate=packed["task_completion_rate"],
        sleep_hours=existing.sleep_hours,
        sleep_quality=existing.sleep_quality,
        mood_morning=existing.mood_morning,
        journal_entry=review,
        takeaway=takeaway,
        one_lesson=takeaway,
        morning_completed=True,
        evening_completed=True,
      )
      log_repo.upsert_by_date(data)
      if takeaway:
        from services.memory_service import MemoryService
        MemoryService().store(takeaway, "commitment", 0.7, today, "journal")
      st.toast("Day closed. See you tomorrow.", icon="🌙")
      st.rerun()

    if existing and existing.evening_completed:
      stats = log_task_stats(existing)
      if stats["total"]:
        hero_card(
          "Today's score",
          f"{stats['completed']}/{stats['total']} tasks · {stats['rate']}%",
        )
