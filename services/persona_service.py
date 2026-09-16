"""User-tunable coach persona: preset tone presets plus free-form prompt directives."""

from __future__ import annotations

from typing import Optional

from database.connection import get_db

# Preset tones exposed in Settings. Keys are the stored values; the text is injected
# verbatim into the coordinator system prompt.
TONE_PRESETS: dict[str, str] = {
  "executive_mentor": (
    "Speak as a seasoned executive mentor: calm, strategic, and outcome-oriented. "
    "Frame advice around leverage, sequencing, and second-order consequences."
  ),
  "socratic_inquirer": (
    "Speak as a Socratic inquirer: lead with sharp diagnostic questions before offering conclusions, "
    "and let the user reason their way to the answer."
  ),
  "direct_accountability": (
    "Speak as a direct accountability partner: blunt, warm, and unsparing about slippage. "
    "Name avoided work explicitly and ask for a concrete commitment."
  ),
}

DEFAULT_TONE = "executive_mentor"

MAX_CUSTOM_PROMPT_CHARS = 2000


class PersonaService:
  """Load the user's persona preferences and render them as prompt directives."""

  def get_persona(self) -> dict[str, Optional[str]]:
    try:
      with get_db() as conn:
        row = conn.execute(
          "SELECT preferred_tone, custom_coach_prompt FROM user WHERE id = 1"
        ).fetchone()
    except Exception:
      # Persona is a preference layer, never a hard dependency of coaching.
      return {"preferred_tone": None, "custom_coach_prompt": None}
    if not row:
      return {"preferred_tone": None, "custom_coach_prompt": None}
    return {
      "preferred_tone": row["preferred_tone"],
      "custom_coach_prompt": row["custom_coach_prompt"],
    }

  def build_directives(self) -> str:
    """Render a PERSONA DIRECTIVES block, or an empty string when nothing is configured."""
    persona = self.get_persona()
    tone = (persona.get("preferred_tone") or "").strip()
    custom = (persona.get("custom_coach_prompt") or "").strip()

    lines: list[str] = []
    tone_text = TONE_PRESETS.get(tone)
    if tone_text:
      lines.append(f"- Tone: {tone_text}")
    if custom:
      lines.append(f"- User-authored directives: {custom[:MAX_CUSTOM_PROMPT_CHARS]}")

    if not lines:
      return ""
    body = "\n".join(lines)
    return (
      "\nPERSONA DIRECTIVES (user-configured; shape delivery only — they never override "
      f"grounding in real user data):\n{body}\n"
    )
