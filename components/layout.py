"""Reusable layout helpers for GoalOS pages."""

import html

import plotly.graph_objects as go
import streamlit as st

from components.theme import COLORS, PLOTLY_LAYOUT

NAV_ITEMS = [
  ("pages/1_Life_Calendar.py", "Life Calendar"),
  ("pages/3_Weekly_Sync.py", "Weekly Sync"),
  ("pages/2_Vision_Goals.py", "Goals"),
  ("pages/5_Weekly_Review.py", "Weekly Review"),
  ("pages/6_History.py", "History"),
  ("pages/8_Settings.py", "Settings"),
]


def top_nav():
  """Centered website-style top navigation bar."""
  st.markdown('<div class="goalos-topnav-shell">', unsafe_allow_html=True)
  _, brand, _ = st.columns([4, 2, 4])
  with brand:
    st.page_link("app.py", label="GoalOS", icon="🎯", use_container_width=True)
  _, nav, _ = st.columns([0.2, 11.6, 0.2])
  with nav:
    cols = st.columns(len(NAV_ITEMS))
    for col, (path, label) in zip(cols, NAV_ITEMS):
      with col:
        st.page_link(path, label=label, use_container_width=True)
  st.markdown("</div>", unsafe_allow_html=True)


def page_header(title: str, subtitle: str = ""):
  sub = f"<p>{html.escape(subtitle)}</p>" if subtitle else ""
  st.markdown(
    f'<div class="goalos-page-header"><h1>{html.escape(title)}</h1>{sub}</div>',
    unsafe_allow_html=True,
  )


def section(title: str):
  st.markdown(f'<div class="goalos-section"><h3>{html.escape(title)}</h3></div>', unsafe_allow_html=True)


def hero_card(label: str, text: str):
  st.markdown(
    f'<div class="goalos-hero">'
    f'<div class="goalos-hero-label">{html.escape(label)}</div>'
    f'<p class="goalos-hero-text">{html.escape(text)}</p>'
    f"</div>",
    unsafe_allow_html=True,
  )


def stat_card(label: str, value: str | int | float, delta: float | None = None):
  delta_html = ""
  if delta is not None:
    direction = "up" if delta >= 0 else "down"
    sign = "+" if delta >= 0 else ""
    delta_html = f'<div class="goalos-stat-delta {direction}">{sign}{delta:.0f} vs prior</div>'
  st.markdown(
    f'<div class="goalos-stat">'
    f'<div class="goalos-stat-label">{html.escape(label)}</div>'
    f'<div class="goalos-stat-value">{html.escape(str(value))}</div>'
    f"{delta_html}"
    f"</div>",
    unsafe_allow_html=True,
  )


def info_card(text: str, variant: str = "default"):
  accent = {
    "success": "goalos-card-success",
    "warning": "goalos-card-warning",
    "danger": "goalos-card-danger",
    "accent": "goalos-card-accent",
  }.get(variant, "")
  st.markdown(
    f'<div class="goalos-card {accent}"><p style="margin:0;color:{COLORS["text"]};">{html.escape(text)}</p></div>',
    unsafe_allow_html=True,
  )


def empty_state(title: str, body: str):
  st.markdown(
    f'<div class="goalos-empty">'
    f"<h4>{html.escape(title)}</h4>"
    f"<p style='margin:0'>{html.escape(body)}</p>"
    f"</div>",
    unsafe_allow_html=True,
  )


def nav_card(title: str, body: str):
  st.markdown(
    f'<div class="goalos-nav-card">'
    f"<h4>{html.escape(title)}</h4>"
    f"<p>{html.escape(body)}</p>"
    f"</div>",
    unsafe_allow_html=True,
  )


def coaching_block(label: str, text: str):
  if not text:
    return
  st.markdown(
    f'<div class="goalos-coach-item">'
    f'<div class="goalos-coach-label">{html.escape(label)}</div>'
    f"{html.escape(text)}"
    f"</div>",
    unsafe_allow_html=True,
  )


def mentor_panel(mentor: dict, show_goal: bool = True):
  """Render mentor rule with clear AI vs fallback status."""
  if not mentor.get("mentor_rule"):
    return

  source = mentor.get("source", "ai")
  if source in ("ai", "ai_agent"):
    model = mentor.get("model", "OpenRouter")
    info_card(f"✓ Live AI — {model}", "success")
    if mentor.get("generated_at"):
      st.caption(f"Generated at {mentor['generated_at'][:19].replace('T', ' ')} UTC")
  elif source == "personalized_fallback":
    reason = mentor.get("fallback_reason", "ai_unavailable")
    detail = mentor.get("fallback_detail", "")
    labels = {
      "no_api_key": "No API key",
      "invalid_api_key": "Invalid API key",
      "insufficient_credits": "No OpenRouter credits",
      "model_not_found": "Model not found",
      "api_error": "API error",
      "invalid_response": "Bad AI response",
    }
    label = labels.get(reason, reason)
    msg = f"Not AI — journal-based rule. Reason: {label}"
    if detail:
      msg += f" ({detail})"
    info_card(msg, "warning")
  else:
    info_card("Not AI — generic fallback. Set API key in Settings and import journal history.", "danger")

  hero_card("Mentor Rule", mentor["mentor_rule"])
  coaching_block("Why", mentor.get("why_this_rule", ""))
  coaching_block("Pattern called out", mentor.get("past_mistake_called_out", ""))
  if show_goal:
    coaching_block("Goal connection", mentor.get("goal_connection", ""))
  coaching_block("If you ignore this", mentor.get("if_you_ignore_this", ""))


def style_chart(fig: go.Figure, height: int = 260, y_range: tuple | None = (0, 100)) -> go.Figure:
  fig.update_layout(**PLOTLY_LAYOUT, height=height)
  if y_range:
    fig.update_yaxes(range=list(y_range))
  fig.update_traces(marker_line_width=0)
  return fig
