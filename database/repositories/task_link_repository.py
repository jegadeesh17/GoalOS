"""Task link repository: one row per task wording (see services/task_link_service.py for the key)."""

from typing import Optional

from database.connection import get_db
from database.repositories._helpers import row_to_dict
from models.task_link import TaskLink, TaskLinkWrite


class TaskLinkRepository:
  """CRUD for task_links."""

  def get_all(self) -> dict[str, TaskLink]:
    with get_db() as conn:
      rows = conn.execute("SELECT task_key, kind, goal_id, updated_at FROM task_links").fetchall()
    links: dict[str, TaskLink] = {}
    for row in rows:
      data = row_to_dict(row)
      data["key"] = data.pop("task_key")
      links[data["key"]] = TaskLink(**data)
    return links

  def upsert(self, link: TaskLinkWrite) -> None:
    with get_db() as conn:
      conn.execute(
        "INSERT INTO task_links (task_key, kind, goal_id) VALUES (?, ?, ?) "
        "ON CONFLICT(task_key) DO UPDATE SET kind=excluded.kind, goal_id=excluded.goal_id, "
        "updated_at=CURRENT_TIMESTAMP",
        (link.key, link.kind, link.goal_id),
      )

  def delete(self, key: str) -> bool:
    with get_db() as conn:
      cursor = conn.execute("DELETE FROM task_links WHERE task_key = ?", (key,))
    return cursor.rowcount > 0

  def get(self, key: str) -> Optional[TaskLink]:
    return self.get_all().get(key)
