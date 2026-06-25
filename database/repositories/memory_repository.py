"""Memory repository."""

from datetime import date
from typing import Optional

from database.connection import get_db
from database.repositories._helpers import build_update, row_to_dict
from models.memory import Memory, MemoryCreate


class MemoryRepository:
  """CRUD operations for memories."""

  def create(self, memory: MemoryCreate) -> Memory:
    data = memory.model_dump()
    with get_db() as conn:
      columns = ", ".join(data.keys())
      placeholders = ", ".join("?" * len(data))
      cursor = conn.execute(
        f"INSERT INTO memories ({columns}) VALUES ({placeholders})",
        list(data.values()),
      )
      memory_id = cursor.lastrowid
      row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
    return Memory(**row_to_dict(row))

  def get_by_id(self, memory_id: int) -> Optional[Memory]:
    with get_db() as conn:
      row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
    return Memory(**row_to_dict(row)) if row else None

  def get_all(self, memory_type: Optional[str] = None) -> list[Memory]:
    query = "SELECT * FROM memories WHERE 1=1"
    params: list = []
    if memory_type:
      query += " AND type = ?"
      params.append(memory_type)
    query += " ORDER BY importance DESC, created_at DESC"
    with get_db() as conn:
      rows = conn.execute(query, params).fetchall()
    return [Memory(**row_to_dict(r)) for r in rows]

  def get_by_type(self, memory_type: str) -> list[Memory]:
    return self.get_all(memory_type=memory_type)

  def get_commitments(self, pending_only: bool = True) -> list[Memory]:
    commitments = self.get_by_type("commitment")
    if not pending_only:
      return commitments
    return [m for m in commitments if m.access_count < 1]

  def increment_access(self, memory_id: int) -> None:
    with get_db() as conn:
      conn.execute(
        """UPDATE memories SET access_count = access_count + 1,
           last_accessed = CURRENT_TIMESTAMP WHERE id = ?""",
        (memory_id,),
      )

  def update(self, memory_id: int, **kwargs) -> Optional[Memory]:
    set_clause, values = build_update(kwargs)
    if not set_clause:
      return self.get_by_id(memory_id)
    values.append(memory_id)
    with get_db() as conn:
      conn.execute(f"UPDATE memories SET {set_clause} WHERE id = ?", values)
    return self.get_by_id(memory_id)

  def delete(self, memory_id: int) -> bool:
    with get_db() as conn:
      cursor = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
    return cursor.rowcount > 0

  def count(self) -> int:
    with get_db() as conn:
      row = conn.execute("SELECT COUNT(*) FROM memories").fetchone()
    return row[0]

  def search_text(self, query: str, limit: int = 20) -> list[Memory]:
    with get_db() as conn:
      rows = conn.execute(
        "SELECT * FROM memories WHERE text LIKE ? ORDER BY importance DESC LIMIT ?",
        (f"%{query}%", limit),
      ).fetchall()
    return [Memory(**row_to_dict(r)) for r in rows]
