"""Persisted user preferences that must not live in source-controlled .env files."""

from database.connection import get_db


class SettingsService:
  REMOTE_AI_CONSENT = "remote_ai_consent"

  def get(self, key: str, default: str = "") -> str:
    with get_db() as conn:
      row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default

  def set(self, key: str, value: str) -> None:
    with get_db() as conn:
      conn.execute(
        "INSERT INTO settings(key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP",
        (key, value),
      )

  def remote_ai_allowed(self) -> bool:
    return self.get(self.REMOTE_AI_CONSENT, "false").lower() == "true"

  def set_remote_ai_allowed(self, allowed: bool) -> None:
    self.set(self.REMOTE_AI_CONSENT, "true" if allowed else "false")
