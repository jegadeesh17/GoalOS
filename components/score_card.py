"""Score card component."""

from components.layout import info_card, stat_card


def render_score_card(title: str, value: float, delta: float = None, interpretation: str = ""):
  stat_card(title, f"{value:.0f}", delta)
  if interpretation:
    info_card(interpretation, variant="accent")
