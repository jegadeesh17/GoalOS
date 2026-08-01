"""Memory repository."""

from typing import Optional

from database.connection import get_db
from database.repositories._helpers import build_update, row_to_dict
from models.memory import Memory, MemoryCreate


class MemoryRepository:
  """CRUD operations for memories."""

  def create(self, memory: MemoryCreate) -> Memory:
    data = memory.model_dump(mode="json")
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

  def get_all(self, memory_type: Optional[str] = None, status: Optional[str] = None) -> list[Memory]:
    query = "SELECT * FROM memories WHERE 1=1"
    params: list = []
    if memory_type:
      query += " AND type = ?"
      params.append(memory_type)
    if status:
      query += " AND status = ?"
      params.append(status)
    query += " ORDER BY importance DESC, created_at DESC"
    with get_db() as conn:
      rows = conn.execute(query, params).fetchall()
    return [Memory(**row_to_dict(r)) for r in rows]

  def get_by_type(self, memory_type: str, status: Optional[str] = "active") -> list[Memory]:
    return self.get_all(memory_type=memory_type, status=status)

  def get_by_hash(self, content_hash: str, source_type: Optional[str], source_id: Optional[int]) -> Optional[Memory]:
    with get_db() as conn:
      row = conn.execute(
        "SELECT * FROM memories WHERE content_hash = ? AND source_type IS ? AND source_id IS ? ORDER BY id DESC LIMIT 1",
        (content_hash, source_type, source_id),
      ).fetchone()
    return Memory(**row_to_dict(row)) if row else None

  def get_commitments(self, pending_only: bool = True) -> list[Memory]:
    commitments = self.get_by_type("commitment", status="active")
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

  def mark_index_status(self, memory_id: int, status: str, indexed: bool = False) -> Optional[Memory]:
    values = {"index_status": status}
    if indexed:
      values["indexed_at"] = "CURRENT_TIMESTAMP"
    with get_db() as conn:
      if indexed:
        conn.execute("UPDATE memories SET index_status = ?, indexed_at = CURRENT_TIMESTAMP WHERE id = ?", (status, memory_id))
      else:
        conn.execute("UPDATE memories SET index_status = ? WHERE id = ?", (status, memory_id))
    return self.get_by_id(memory_id)

  def delete(self, memory_id: int) -> bool:
    with get_db() as conn:
      cursor = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
    return cursor.rowcount > 0

  def count(self, status: Optional[str] = None) -> int:
    with get_db() as conn:
      if status:
        row = conn.execute("SELECT COUNT(*) FROM memories WHERE status = ?", (status,)).fetchone()
      else:
        row = conn.execute("SELECT COUNT(*) FROM memories").fetchone()
    return row[0]

  def search_text(self, query: str, limit: int = 20) -> list[Memory]:
    with get_db() as conn:
      tokens = [token for token in query.replace("'", " ").split() if token]
      if tokens:
        match = " OR ".join(f'"{token}"' for token in tokens[:12])
        rows = conn.execute(
          "SELECT m.* FROM memory_fts f JOIN memories m ON m.id = f.memory_id "
          "WHERE memory_fts MATCH ? AND m.status = 'active' ORDER BY m.importance DESC LIMIT ?",
          (match, limit),
        ).fetchall()
      else:
        rows = []
    return [Memory(**row_to_dict(r)) for r in rows]
