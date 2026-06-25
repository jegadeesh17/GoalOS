"""Database schema migrations."""

from database.connection import get_connection

SCHEMA = """
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    life_vision TEXT,
    five_year_vision TEXT,
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def run_migrations() -> None:
  """Create all database tables."""
  conn = get_connection()
  try:
    conn.executescript(SCHEMA)
    cursor = conn.execute("SELECT COUNT(*) FROM user")
    if cursor.fetchone()[0] == 0:
      conn.execute(
        "INSERT INTO user (id, name) VALUES (1, 'User')"
      )
    for col in ("one_year_vision",):
      try:
        conn.execute(f"ALTER TABLE user ADD COLUMN {col} TEXT")
      except Exception:
        pass
    conn.commit()
  finally:
    conn.close()


if __name__ == "__main__":
  run_migrations()
  print("Migrations complete.")
