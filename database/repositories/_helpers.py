"""Shared repository utilities."""

import sqlite3
from datetime import date, datetime
from typing import Any


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
  """Convert sqlite Row to dict with proper types."""
  return {key: row[key] for key in row.keys()}


def _serialize_value(value: Any) -> Any:
  if isinstance(value, (date, datetime)):
    return value.isoformat()
  if isinstance(value, bool):
    return int(value)
  return value


def build_insert(data: dict[str, Any]) -> tuple[str, list[Any]]:
  """Build INSERT SQL from a data dict."""
  filtered = {k: _serialize_value(v) for k, v in data.items() if v is not None}
  columns = ", ".join(filtered.keys())
  placeholders = ", ".join("?" * len(filtered))
  return f"INSERT INTO {{table}} ({columns}) VALUES ({placeholders})", list(filtered.values())


def build_update(data: dict[str, Any]) -> tuple[str, list[Any]]:
  """Build SET clause for UPDATE."""
  filtered = {k: _serialize_value(v) for k, v in data.items() if v is not None}
  set_clause = ", ".join(f"{k} = ?" for k in filtered)
  return set_clause, list(filtered.values())
