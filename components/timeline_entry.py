"""Timeline entry component."""

import html
from datetime import date

import streamlit as st

from components.theme import COLORS

_TYPE_STYLE = {
  "log": ("goalos-card-accent", "Daily Log"),
  "weekly": ("goalos-card-success", "Weekly Review"),
  "memory": ("goalos-card-warning", "Memory"),
  "coaching": ("", "Coaching"),
}


def render_timeline_entry(entry_type: str, entry_date: date, content: str, metadata: dict = None):
  style, label = _TYPE_STYLE.get(entry_type, ("", entry_type.title()))
  meta_html = ""
  if metadata:
    parts = " · ".join(f"{html.escape(str(k))}: {html.escape(str(v))}" for k, v in metadata.items())
    meta_html = f'<p style="margin:0.35rem 0 0;font-size:0.78rem;color:{COLORS["muted"]};">{parts}</p>'
  preview = content[:500] + ("..." if len(content) > 500 else "")
  st.markdown(
    f'<div class="goalos-card {style}">'
    f'<p style="margin:0;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.08em;color:{COLORS["accent"]};">'
    f"{label} · {entry_date}"
    f"</p>"
    f'<p style="margin:0.5rem 0 0;color:{COLORS["text"]};line-height:1.55;">{html.escape(preview)}</p>'
    f"{meta_html}"
    f"</div>",
    unsafe_allow_html=True,
  )
