"""Portable export and safe local backups for single-user GoalOS data."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from config.settings import settings
from database.connection import get_db

EXPORT_TABLES = (
  "user", "goals", "milestones", "daily_logs", "weekly_reviews",
  "scores", "memories", "coach_responses", "settings",
)


class DataPortabilityService:
  def export_payload(self) -> dict:
    """Return a serializable complete user-data snapshot."""
    payload = {
      "format": "goalos-export",
      "version": 1,
      "exported_at": datetime.now(timezone.utc).isoformat(),
      "tables": {},
    }
    with get_db() as conn:
      for table in EXPORT_TABLES:
        rows = conn.execute(f"SELECT * FROM {table}").fetchall()
        payload["tables"][table] = [dict(row) for row in rows]
    return payload

  def export_json(self) -> str:
    return json.dumps(self.export_payload(), indent=2, default=str)

  def create_backup(self) -> Path:
    """Write a timestamped zip outside the project data paths before destructive work."""
    root = Path(settings.DB_PATH).resolve().parent / "backups"
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = root / f"goalos-backup-{stamp}.zip"
    with ZipFile(backup_path, "w", ZIP_DEFLATED) as archive:
      archive.writestr("goalos-export.json", self.export_json())
      db_path = Path(settings.DB_PATH)
      if db_path.exists():
        archive.write(db_path, "goalos.db")
      chroma_path = Path(settings.CHROMA_PATH)
      if chroma_path.exists():
        for path in chroma_path.rglob("*"):
          if path.is_file():
            archive.write(path, Path("chroma_db") / path.relative_to(chroma_path))
    return backup_path

  def clear_all_data(self) -> Path:
    """Back up first, then delete local stores. Caller reinitializes migrations."""
    backup = self.create_backup()
    db_path = Path(settings.DB_PATH)
    chroma_path = Path(settings.CHROMA_PATH)
    if db_path.exists():
      db_path.unlink()
    if chroma_path.exists():
      shutil.rmtree(chroma_path)
    return backup
