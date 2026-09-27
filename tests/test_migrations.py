"""Migration regression tests."""

from database.connection import get_connection
from database.migrations import (
  _add_column,
  _columns,
  _migration_7_goals_are_the_vision_source_of_truth,
)

VISION_COLUMNS = {"life_vision", "five_year_vision", "one_year_vision"}


class TestVisionColumnDropMigration:
  def test_drops_legacy_vision_columns_when_present(self, temp_db):
    conn = get_connection()
    try:
      for col in VISION_COLUMNS:
        _add_column(conn, "user", f"{col} TEXT")
      assert VISION_COLUMNS <= _columns(conn, "user")

      _migration_7_goals_are_the_vision_source_of_truth(conn)
      conn.commit()

      assert not (VISION_COLUMNS & _columns(conn, "user"))
    finally:
      conn.close()

  def test_is_a_noop_when_columns_already_absent(self, temp_db):
    conn = get_connection()
    try:
      _migration_7_goals_are_the_vision_source_of_truth(conn)
      conn.commit()
      assert not (VISION_COLUMNS & _columns(conn, "user"))
    finally:
      conn.close()
