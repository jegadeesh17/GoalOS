"""Daily planning and reflection with task-to-goal links."""

import json
import os
import sys
import uuid
from datetime import date

_APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _APP_DIR not in sys.path:
  sys.path.insert(0, _APP_DIR)
import bootstrap  # noqa: F401

import streamlit as st

from components.layout import hero_card, info_card, mentor_panel, page_header, section
from config.settings import settings
from database.repositories.goal_repository import GoalRepository
from database.repositories.log_repository import LogRepository
from database.repositories.milestone_repository import MilestoneRepository
from models.daily_log import DailyLogUpdate
from services.journal_helpers import ensure_task_ids, load_tasks_from_log, log_task_stats, normalize_tasks, pack_tasks, serialize_journal_fields
from services.settings_service import SettingsService
from utils import configure_page, get_coach_service, init_app

configure_page("Today's Journal | GoalOS", "📓")
init_app()

today = date.today()
log_repo, goal_repo, milestone_repo = LogRepository(), GoalRepository(), MilestoneRepository()
coach, privacy = get_coach_service(), SettingsService()
existing = log_repo.get_by_date(today)
task_state_key = f"tasks_{today.isoformat()}"


def _plans_text() -> str:
  if not existing or not existing.time_blocks:
    return ""
  try:
    blocks = json.loads(existing.time_blocks)
    if isinstance(blocks, list):
      return "\n".join(f"{item['start']} - {item['end']}: {item['activity']}" for item in blocks if isinstance(item, dict))
  except (json.JSONDecodeError, TypeError):
    pass
  return existing.time_blocks


def _tasks() -> list[dict]:
  if task_state_key not in st.session_state:
    st.session_state[task_state_key] = ensure_task_ids(load_tasks_from_log(existing))
  return ensure_task_ids(st.session_state[task_state_key])


def _task_editor() -> list[dict]:
  tasks = _tasks()
  goals = goal_repo.get_active()
  milestones = milestone_repo.get_active()
  goal_options = {0: "No goal", **{goal.id: goal.title for goal in goals}}
  section("Tasks")
  st.caption("Rank tasks and optionally link each one to a goal or milestone.")
  for index, task in enumerate(tasks):
    cols = st.columns([0.4, 4.0, 1.5, 1.5, 0.45])
    with cols[0]:
      st.caption(f"#{index + 1}")
    with cols[1]:
      task["text"] = st.text_input("Task", task.get("text", ""), key=f"task_text_{task['id']}", label_visibility="collapsed")
    with cols[2]:
      goal_id = int(task.get("goal_id") or 0)
      goal_id = goal_id if goal_id in goal_options else 0
      goal_id = st.selectbox("Goal", list(goal_options), index=list(goal_options).index(goal_id), format_func=lambda value: goal_options[value], key=f"task_goal_{task['id']}", label_visibility="collapsed")
      if goal_id:
        task["goal_id"] = goal_id
      else:
        task.pop("goal_id", None)
    with cols[3]:
      valid_milestones = [m for m in milestones if not task.get("goal_id") or m.goal_id == task["goal_id"]]
      milestone_options = {0: "No milestone", **{m.id: m.title for m in valid_milestones}}
      milestone_id = int(task.get("milestone_id") or 0)
      milestone_id = milestone_id if milestone_id in milestone_options else 0
      milestone_id = st.selectbox("Milestone", list(milestone_options), index=list(milestone_options).index(milestone_id), format_func=lambda value: milestone_options[value], key=f"task_milestone_{task['id']}", label_visibility="collapsed")
      if milestone_id:
        task["milestone_id"] = milestone_id
      else:
        task.pop("milestone_id", None)
    with cols[4]:
      if st.button("Remove", key=f"remove_{task['id']}"):
        st.session_state[task_state_key] = [item for item in tasks if item["id"] != task["id"]]
        st.rerun()
  if st.button("Add task"):
    tasks.append({"id": uuid.uuid4().hex[:8], "text": "", "completed": False, "priority": len(tasks) + 1})
    st.session_state[task_state_key] = tasks
    st.rerun()
  st.session_state[task_state_key] = tasks
  return normalize_tasks(tasks)


page_header("Today's Journal", today.strftime("%A, %d %B %Y"))
morning_tab, evening_tab = st.tabs(["Morning", "Evening"])

with morning_tab:
  if not privacy.remote_ai_allowed():
    info_card("Remote AI is off. Saving a morning plan creates a local, journal-based rule. Enable consent in Settings to use OpenRouter.", "warning")
  elif not settings.OPENROUTER_API_KEY:
    info_card("Remote AI consent is enabled, but no OpenRouter key is configured. A local fallback will be used.", "warning")
  gratitude = st.text_input("Gratitude", value=existing.gratitude if existing else "")
  c1, c2, c3 = st.columns(3)
  with c1:
    sleep_hours = st.number_input("Sleep hours", min_value=0.0, max_value=24.0, value=float(existing.sleep_hours) if existing and existing.sleep_hours is not None else 7.0, step=0.5)
  with c2:
    sleep_quality = st.slider("Sleep quality", 1, 5, existing.sleep_quality if existing and existing.sleep_quality else 3)
  with c3:
    mood_morning = st.slider("Mood", 1, 5, existing.mood_morning if existing and existing.mood_morning else 3)
  morning_tasks = _task_editor()
  plans = st.text_area("Time slots (optional)", value=_plans_text(), placeholder="09:00-10:30: Deep work")

  if existing and existing.morning_ai_output:
    try:
      mentor = json.loads(existing.morning_ai_output)
      if mentor.get("mentor_rule"):
        section("Today's Rule")
        mentor_panel(mentor)
        if mentor.get("evidence"):
          st.caption("Evidence: " + ", ".join(item.get("goal_title") or f"memory #{item.get('memory_id')}" for item in mentor["evidence"] if item.get("goal_title") or item.get("memory_id")))
    except json.JSONDecodeError:
      pass

  if st.button("Save Morning and Get Mentor Rule", type="primary", use_container_width=True):
    if not morning_tasks:
      st.error("Add at least one task.")
    else:
      try:
        fields = serialize_journal_fields(gratitude, plans, morning_tasks)
        log = log_repo.upsert_fields(today, DailyLogUpdate(morning_completed=True, sleep_hours=sleep_hours, sleep_quality=sleep_quality, mood_morning=mood_morning, **fields))
        with st.spinner("Preparing your mentor rule..."):
          coach.get_morning_coaching(today, log)
        st.session_state.pop(task_state_key, None)
        st.toast("Morning saved.", icon="✅")
        st.rerun()
      except ValueError as exc:
        st.error(str(exc))
      except Exception:
        st.error("Your entry was saved, but coaching could not be generated.")

with evening_tab:
  if not existing or not existing.morning_completed:
    info_card("Complete the morning plan before closing the day.", "warning")
  else:
    tasks = load_tasks_from_log(existing)
    section("Task review")
    updated_tasks = []
    for task in tasks:
      completed = st.checkbox(f"#{task['priority']} {task['text']}", value=task.get("completed", False), key=f"done_{task.get('id', task['priority'])}")
      updated_tasks.append({**task, "completed": completed})
    stats = log_task_stats(existing)
    if stats["total"]:
      hero_card("Current task status", f"{stats['completed']}/{stats['total']} complete")
    review = st.text_area("Review", value=existing.journal_entry or "", height=140)
    takeaway = st.text_input("Takeaway", value=existing.takeaway or "")
    if st.button("Close the Day", type="primary", use_container_width=True):
      packed = pack_tasks(updated_tasks)
      log = log_repo.upsert_fields(today, DailyLogUpdate(**packed, journal_entry=review or None, takeaway=takeaway or None, one_lesson=takeaway or None, evening_completed=True))
      try:
        coach.get_evening_coaching(today, log)
      except Exception:
        st.warning("Day saved, but the optional coaching summary could not be generated.")
      st.toast("Day closed.", icon="✅")
      st.rerun()
