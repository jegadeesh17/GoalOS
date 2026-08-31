"""Repository for coach sessions, messages, and blackboard state."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from database.connection import get_db
from database.repositories._helpers import row_to_dict
from models.coach_session import CoachMessageRead, CoachSessionRead


class CoachSessionRepository:
  """Persistence for agentic conversation sessions and multi-turn message history."""

  def create_session(
    self,
    title: Optional[str] = None,
    intent: Optional[str] = None,
    active_horizon_id: Optional[str] = None,
    blackboard: Optional[dict[str, Any]] = None,
    session_id: Optional[str] = None,
  ) -> CoachSessionRead:
    sid = session_id or f"sess_{uuid.uuid4().hex[:12]}"
    session_title = title or f"Coaching Session {datetime.now(timezone.utc).strftime('%b %d, %H:%M')}"
    bb_json = json.dumps(blackboard or {})
    now = datetime.now(timezone.utc).isoformat()

    with get_db() as conn:
      conn.execute(
        """
        INSERT INTO coach_sessions (id, title, intent, active_horizon_id, blackboard, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (sid, session_title, intent, active_horizon_id, bb_json, now, now),
      )

    return CoachSessionRead(
      id=sid,
      title=session_title,
      intent=intent,
      active_horizon_id=active_horizon_id,
      blackboard=blackboard or {},
      created_at=now,
      updated_at=now,
      messages=[],
    )

  def get_session(self, session_id: str) -> Optional[CoachSessionRead]:
    with get_db() as conn:
      s_row = conn.execute("SELECT * FROM coach_sessions WHERE id = ?", (session_id,)).fetchone()
      if not s_row:
        return None
      s_dict = row_to_dict(s_row)

      m_rows = conn.execute(
        "SELECT * FROM coach_messages WHERE session_id = ? ORDER BY created_at ASC, rowid ASC",
        (session_id,),
      ).fetchall()

    messages: list[CoachMessageRead] = []
    for m in m_rows:
      m_dict = row_to_dict(m)
      tool_calls = json.loads(m_dict.get("tool_calls") or "[]")
      citations = json.loads(m_dict.get("citations") or "[]")
      messages.append(
        CoachMessageRead(
          id=m_dict["id"],
          session_id=m_dict["session_id"],
          role=m_dict["role"],
          content=m_dict["content"],
          agent_name=m_dict.get("agent_name"),
          tool_calls=tool_calls if isinstance(tool_calls, list) else [],
          citations=citations if isinstance(citations, list) else [],
          created_at=str(m_dict.get("created_at") or ""),
        )
      )

    bb_raw = s_dict.get("blackboard")
    blackboard = json.loads(bb_raw) if bb_raw and isinstance(bb_raw, str) else (bb_raw or {})

    return CoachSessionRead(
      id=s_dict["id"],
      title=s_dict["title"],
      intent=s_dict.get("intent"),
      active_horizon_id=s_dict.get("active_horizon_id"),
      blackboard=blackboard if isinstance(blackboard, dict) else {},
      created_at=str(s_dict.get("created_at") or ""),
      updated_at=str(s_dict.get("updated_at") or ""),
      messages=messages,
    )

  def list_sessions(self, limit: int = 50) -> list[CoachSessionRead]:
    with get_db() as conn:
      rows = conn.execute(
        "SELECT * FROM coach_sessions ORDER BY updated_at DESC LIMIT ?", (limit,)
      ).fetchall()

    sessions: list[CoachSessionRead] = []
    for r in rows:
      r_dict = row_to_dict(r)
      bb_raw = r_dict.get("blackboard")
      blackboard = json.loads(bb_raw) if bb_raw and isinstance(bb_raw, str) else (bb_raw or {})
      sessions.append(
        CoachSessionRead(
          id=r_dict["id"],
          title=r_dict["title"],
          intent=r_dict.get("intent"),
          active_horizon_id=r_dict.get("active_horizon_id"),
          blackboard=blackboard if isinstance(blackboard, dict) else {},
          created_at=str(r_dict.get("created_at") or ""),
          updated_at=str(r_dict.get("updated_at") or ""),
          messages=[],
        )
      )
    return sessions

  def update_blackboard(self, session_id: str, blackboard: dict[str, Any]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    bb_json = json.dumps(blackboard)
    with get_db() as conn:
      conn.execute(
        "UPDATE coach_sessions SET blackboard = ?, updated_at = ? WHERE id = ?",
        (bb_json, now, session_id),
      )

  def update_session_meta(
    self,
    session_id: str,
    title: Optional[str] = None,
    intent: Optional[str] = None,
    active_horizon_id: Optional[str] = None,
  ) -> None:
    updates: list[str] = ["updated_at = ?"]
    params: list[Any] = [datetime.now(timezone.utc).isoformat()]
    if title is not None:
      updates.append("title = ?")
      params.append(title)
    if intent is not None:
      updates.append("intent = ?")
      params.append(intent)
    if active_horizon_id is not None:
      updates.append("active_horizon_id = ?")
      params.append(active_horizon_id)
    params.append(session_id)

    with get_db() as conn:
      conn.execute(
        f"UPDATE coach_sessions SET {', '.join(updates)} WHERE id = ?",
        params,
      )

  def append_message(
    self,
    session_id: str,
    role: str,
    content: str,
    agent_name: Optional[str] = None,
    tool_calls: Optional[list[dict[str, Any]]] = None,
    citations: Optional[list[dict[str, Any]]] = None,
  ) -> CoachMessageRead:
    mid = f"msg_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    tools_json = json.dumps(tool_calls or [])
    cites_json = json.dumps(citations or [])

    with get_db() as conn:
      conn.execute(
        """
        INSERT INTO coach_messages (id, session_id, role, content, agent_name, tool_calls, citations, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (mid, session_id, role, content, agent_name, tools_json, cites_json, now),
      )
      conn.execute(
        "UPDATE coach_sessions SET updated_at = ? WHERE id = ?",
        (now, session_id),
      )

    return CoachMessageRead(
      id=mid,
      session_id=session_id,
      role=role,  # type: ignore[arg-type]
      content=content,
      agent_name=agent_name,
      tool_calls=tool_calls or [],
      citations=citations or [],
      created_at=now,
    )

  def delete_session(self, session_id: str) -> bool:
    with get_db() as conn:
      cursor = conn.execute("DELETE FROM coach_sessions WHERE id = ?", (session_id,))
      return cursor.rowcount > 0
