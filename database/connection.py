"""SQLite database connection management."""

import sqlite3
from contextlib import contextmanager
from typing import Generator

from config.settings import settings


def get_connection() -> sqlite3.Connection:
  """Return a SQLite connection with row factory enabled."""
  conn = sqlite3.connect(settings.DB_PATH, check_same_thread=False)
  conn.row_factory = sqlite3.Row
  conn.execute("PRAGMA foreign_keys = ON")
  return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
  """Context manager for database connections."""
  conn = get_connection()
  try:
    yield conn
    conn.commit()
  except Exception:
    conn.rollback()
    raise
  finally:
    conn.close()
