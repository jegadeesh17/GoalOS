"""Idempotent storage for weekly coaching reviews."""

from datetime import date
from typing import Optional

from database.connection import get_db
from database.repositories._helpers import row_to_dict
from models.weekly_review import WeeklyReview, WeeklyReviewCreate


class WeeklyReviewRepository:
  def upsert(self, review: WeeklyReviewCreate) -> WeeklyReview:
    data = review.model_dump(mode="json")
    with get_db() as conn:
      conn.execute(
        "INSERT INTO weekly_reviews (week_start, week_end, ai_output, is_current) VALUES (?, ?, ?, TRUE) "
        "ON CONFLICT(week_start) WHERE is_current = TRUE DO UPDATE SET "
        "week_end=excluded.week_end, ai_output=excluded.ai_output",
        (data["week_start"], data["week_end"], data["ai_output"]),
      )
      row = conn.execute("SELECT * FROM weekly_reviews WHERE week_start = ? AND is_current = TRUE", (data["week_start"],)).fetchone()
    return WeeklyReview(**row_to_dict(row))

  def get_by_week_start(self, week_start: date) -> Optional[WeeklyReview]:
    with get_db() as conn:
      row = conn.execute("SELECT * FROM weekly_reviews WHERE week_start = ? AND is_current = TRUE", (week_start.isoformat(),)).fetchone()
    return WeeklyReview(**row_to_dict(row)) if row else None
