"""Versioned, additive SQLite migrations for GoalOS."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable

from database.connection import get_connection


BASE_SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    life_vision TEXT,
    five_year_vision TEXT,
    one_year_vision TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    horizon TEXT NOT NULL,
    deadline DATE,
    priority INTEGER DEFAULT 3,
    progress REAL DEFAULT 0.0,
    status TEXT DEFAULT 'active',
    reason TEXT,
    success_criteria TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id INTEGER NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    success_criteria TEXT,
    deadline DATE,
    progress REAL DEFAULT 0.0,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL UNIQUE,
    morning_completed BOOLEAN DEFAULT FALSE,
    sleep_hours REAL,
    sleep_quality INTEGER,
    energy_level INTEGER,
    mood_morning INTEGER,
    expected_focus INTEGER,
    available_hours REAL,
    calendar_constraints TEXT,
    free_write TEXT,
    intention TEXT,
    anxiety TEXT,
    anticipation TEXT,
    top_priority TEXT,
    supporting_task_1 TEXT,
    supporting_task_2 TEXT,
    gratitude TEXT,
    time_blocks TEXT,
    planned_tasks TEXT,
    evening_completed BOOLEAN DEFAULT FALSE,
    journal_entry TEXT,
    tasks_completed TEXT,
    task_completion_rate REAL,
    deep_work_hours REAL,
    workout_completed BOOLEAN,
    workout_notes TEXT,
    biggest_distraction TEXT,
    mood_evening INTEGER,
    one_win TEXT,
    one_lesson TEXT,
    takeaway TEXT,
    morning_ai_output TEXT,
    evening_ai_output TEXT,
    imported BOOLEAN DEFAULT FALSE,
    import_source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS weekly_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    ai_output TEXT,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    scope TEXT NOT NULL,
    goal_alignment_score REAL,
    consistency_score REAL,
    health_score REAL,
    learning_score REAL,
    productivity_score REAL,
    momentum_score REAL,
    overall_growth_score REAL,
    gap_score REAL,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS coach_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_type TEXT NOT NULL,
    user_message TEXT,
    ai_response TEXT NOT NULL,
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    type TEXT NOT NULL,
    importance REAL DEFAULT 0.5,
    source_date DATE,
    source_type TEXT,
    source_id INTEGER,
    recency_score REAL,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    content_hash TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    user_feedback INTEGER,
    index_status TEXT NOT NULL DEFAULT 'pending',
    indexed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
  return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}


def _add_column(conn: sqlite3.Connection, table: str, definition: str) -> None:
  name = definition.split()[0]
  if name not in _columns(conn, table):
    conn.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")


def _migration_1_integrity(conn: sqlite3.Connection) -> None:
  """Upgrade legacy installations to the vNext data model without deleting data."""
  _add_column(conn, "user", "one_year_vision TEXT")
  for definition in (
    "content_hash TEXT",
    "status TEXT NOT NULL DEFAULT 'active'",
    "user_feedback INTEGER",
    "index_status TEXT NOT NULL DEFAULT 'pending'",
    "indexed_at TIMESTAMP",
  ):
    _add_column(conn, "memories", definition)
  _add_column(conn, "scores", "is_current BOOLEAN NOT NULL DEFAULT TRUE")
  _add_column(conn, "weekly_reviews", "is_current BOOLEAN NOT NULL DEFAULT TRUE")
  # Preserve every historical row. Only the latest row is current and subject to
  # idempotent-write uniqueness; older duplicates remain available for audit.
  conn.execute("""UPDATE scores SET is_current = CASE
      WHEN id = (SELECT MAX(s2.id) FROM scores s2 WHERE s2.date = scores.date AND s2.scope = scores.scope)
      THEN TRUE ELSE FALSE END""")
  conn.execute("""UPDATE weekly_reviews SET is_current = CASE
      WHEN id = (SELECT MAX(w2.id) FROM weekly_reviews w2 WHERE w2.week_start = weekly_reviews.week_start)
      THEN TRUE ELSE FALSE END""")
  conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_scores_date_scope_current ON scores(date, scope) WHERE is_current = TRUE")
  conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_weekly_reviews_week_start_current ON weekly_reviews(week_start) WHERE is_current = TRUE")
  conn.execute("CREATE INDEX IF NOT EXISTS ix_memories_status_date ON memories(status, source_date DESC)")
  conn.execute("CREATE INDEX IF NOT EXISTS ix_daily_logs_date ON daily_logs(date DESC)")
  conn.execute("CREATE INDEX IF NOT EXISTS ix_coach_responses_date_type ON coach_responses(date DESC, session_type)")
  conn.execute("""CREATE TABLE IF NOT EXISTS milestones (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      goal_id INTEGER NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
      title TEXT NOT NULL,
      success_criteria TEXT,
      deadline DATE,
      progress REAL DEFAULT 0.0,
      status TEXT DEFAULT 'active',
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
  conn.execute("CREATE INDEX IF NOT EXISTS ix_milestones_goal_status ON milestones(goal_id, status)")


def _migration_2_memory_search(conn: sqlite3.Connection) -> None:
  """Create a local lexical index alongside the semantic Chroma index."""
  conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(text, memory_id UNINDEXED)")
  conn.execute("DELETE FROM memory_fts")
  conn.execute("INSERT INTO memory_fts(rowid, text, memory_id) SELECT id, text, id FROM memories")


MIGRATIONS: list[tuple[int, Callable[[sqlite3.Connection], None]]] = [
  (1, _migration_1_integrity),
  (2, _migration_2_memory_search),
]


def run_migrations() -> None:
  """Apply each unapplied migration in a transaction."""
  conn = get_connection()
  try:
    conn.executescript(BASE_SCHEMA)
    if conn.execute("SELECT COUNT(*) FROM user").fetchone()[0] == 0:
      conn.execute("INSERT INTO user (id, name) VALUES (1, 'User')")
    applied = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
    for version, migration in MIGRATIONS:
      if version not in applied:
        migration(conn)
        conn.execute("INSERT INTO schema_migrations(version) VALUES (?)", (version,))
    conn.commit()
  except Exception:
    conn.rollback()
    raise
  finally:
    conn.close()


if __name__ == "__main__":
  run_migrations()
  print("Migrations complete.")
