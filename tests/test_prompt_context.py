"""The coach prompt gets a slim, compact view of the context; fallbacks keep reading the full dict."""

import json

from ai.pipelines._base import format_context


def test_format_context_drops_duplicate_keys_and_nulls():
  ctx = {
    "date": "2026-10-10",
    "historical_baseline_logs": [{"date": "2026-09-01"}],
    "journal_text_digest": [{"date": "2026-10-09"}],
    "recent_coach_advice": [{"ai_response": "{}"}],
    "current_scores": None,
    "relevant_memories": [],
    "monthly_progress": {"days_logged": 9, "wins": ""},
  }
  out = json.loads(format_context(ctx))
  assert out == {"date": "2026-10-10", "monthly_progress": {"days_logged": 9}}


def test_format_context_slims_logs():
  ctx = {
    "recent_logs": [
      {"id": 5, "date": "2026-10-09", "planned_tasks": "1. exam (tick)", "mood_morning": None, "morning_ai_output": "x"}
    ]
  }
  out = json.loads(format_context(ctx))
  assert set(out["recent_logs"][0]) == {"date", "planned_tasks"}
