"""Memory card component."""

import html

import streamlit as st

from components.theme import COLORS

_TYPE_META = {
  "commitment": ("#f87171", "Commitment"),
  "lesson": ("#fbbf24", "Lesson"),
  "achievement": ("#34d399", "Achievement"),
  "distraction": ("#fb923c", "Distraction"),
  "pattern": ("#38bdf8", "Pattern"),
  "journal_insight": ("#a78bfa", "Insight"),
}


def render_memory_card(memory):
  color, label = _TYPE_META.get(memory.type, (COLORS["muted"], memory.type.title()))
  date_str = f" · {memory.source_date}" if memory.source_date else ""
  st.markdown(
    f'<div class="goalos-card">'
    f'<p style="margin:0;font-size:0.72rem;font-weight:600;color:{color};text-transform:uppercase;letter-spacing:0.06em;">'
    f"{label}{date_str} · importance {memory.importance:.1f}"
    f"</p>"
    f'<p style="margin:0.55rem 0 0;color:{COLORS["text"]};line-height:1.55;">{html.escape(memory.text)}</p>'
    f"</div>",
    unsafe_allow_html=True,
  )
