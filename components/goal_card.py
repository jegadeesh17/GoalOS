"""Goal card component."""

import html

import streamlit as st

from components.theme import COLORS

_CATEGORY_BADGE = {
  "career": "goalos-badge-career",
  "health": "goalos-badge-health",
  "learning": "goalos-badge-learning",
  "personal": "goalos-badge-personal",
  "financial": "goalos-badge-financial",
}


def render_goal_card(goal, show_actions: bool = False):
  badge = _CATEGORY_BADGE.get(goal.category, "goalos-badge-default")
  progress_pct = max(0, min(100, goal.progress * 100))
  reason_html = (
    f'<p style="margin:0.75rem 0 0;color:{COLORS["muted"]};font-size:0.88rem;">'
    f"<strong style='color:{COLORS["text"]};'>Why:</strong> {html.escape(goal.reason)}</p>"
    if goal.reason
    else ""
  )
  desc_html = (
    f'<p style="margin:0.35rem 0 0;color:{COLORS["muted"]};font-size:0.9rem;">{html.escape(goal.description)}</p>'
    if goal.description
    else ""
  )
  st.markdown(
    f'<div class="goalos-card goalos-card-accent">'
    f'<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:0.5rem;">'
    f'<h4 style="margin:0;color:{COLORS["text"]};font-size:1.05rem;">{html.escape(goal.title)}</h4>'
    f'<span class="goalos-badge {badge}">{html.escape(goal.category)}</span>'
    f"</div>"
    f"{desc_html}"
    f'<p style="margin:0.5rem 0 0;font-size:0.78rem;color:{COLORS["muted"]};">'
    f"{html.escape(goal.horizon)} · Priority {goal.priority}"
    f"</p>"
    f'<div class="goalos-progress"><div class="goalos-progress-bar" style="width:{progress_pct:.0f}%;"></div></div>'
    f'<p style="margin:0;font-size:0.78rem;color:{COLORS["muted"]};">{progress_pct:.0f}% complete</p>'
    f"{reason_html}"
    f"</div>",
    unsafe_allow_html=True,
  )
  if show_actions:
    return st.button("Edit", key=f"edit_goal_{goal.id}", use_container_width=True)
