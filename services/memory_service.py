"""SQLite-backed memory lifecycle with repairable Chroma indexing and hybrid retrieval."""

from __future__ import annotations

import hashlib
import logging
import math
from datetime import date
from pathlib import Path
from typing import Optional

from database.repositories.memory_repository import MemoryRepository
from models.memory import Memory, MemoryCreate
from services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)
_COLLECTIONS: dict[str, object | None] = {}


def _collection_key(chroma_path: str) -> str:
  return str(Path(chroma_path).resolve())


def _get_collection(chroma_path: str):
  key = _collection_key(chroma_path)
  if key in _COLLECTIONS:
    return _COLLECTIONS[key]
  try:
    import chromadb
    client = chromadb.PersistentClient(path=key)
    collection = client.get_or_create_collection(name="goalos_memories", metadata={"hnsw:space": "cosine"})
  except Exception as exc:
    logger.warning("ChromaDB unavailable: %s", exc)
    collection = None
  _COLLECTIONS[key] = collection
  return collection


def clear_collection_cache(chroma_path: Optional[str] = None) -> None:
  """Forget stale Chroma clients after reset or path changes."""
  if chroma_path is None:
    _COLLECTIONS.clear()
  else:
    _COLLECTIONS.pop(_collection_key(chroma_path), None)


class MemoryService:
  def __init__(self, chroma_path: Optional[str] = None):
    from config.settings import settings
    self.chroma_path = chroma_path or settings.CHROMA_PATH
    self.repo = MemoryRepository()
    self.embedder = EmbeddingService()
    self._collection = _get_collection(self.chroma_path)

  @staticmethod
  def _content_hash(text: str) -> str:
    normalized = " ".join(text.casefold().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

  def store(self, text: str, memory_type: str, importance: float = 0.5,
            source_date: Optional[date] = None, source_type: Optional[str] = None,
            source_id: Optional[int] = None) -> Memory:
    text = text.strip()
    if not text:
      raise ValueError("Memory text cannot be empty")
    content_hash = self._content_hash(text)
    existing = self.repo.get_by_hash(content_hash, source_type, source_id)
    if existing:
      if existing.status != "active":
        existing = self.repo.update(existing.id, status="active", index_status="pending")
      assert existing is not None
      self._index_memory(existing)
      return existing
    memory = self.repo.create(MemoryCreate(
      text=text, type=memory_type, importance=importance, source_date=source_date,
      source_type=source_type, source_id=source_id, content_hash=content_hash,
    ))
    self._upsert_fts(memory)
    self._index_memory(memory)
    return self.repo.get_by_id(memory.id) or memory

  def _upsert_fts(self, memory: Memory) -> None:
    from database.connection import get_db
    with get_db() as conn:
      conn.execute("INSERT OR REPLACE INTO memory_fts(rowid, text, memory_id) VALUES (?, ?, ?)", (memory.id, memory.text, memory.id))

  def _index_memory(self, memory: Memory) -> bool:
    if self._collection is None:
      self.repo.mark_index_status(memory.id, "pending")
      return False
    try:
      self._collection.upsert(
        ids=[str(memory.id)], embeddings=[self.embedder.embed(memory.text)], documents=[memory.text],
        metadatas=[{"type": memory.type, "importance": memory.importance, "source_date": memory.source_date.isoformat() if memory.source_date else ""}],
      )
      self.repo.mark_index_status(memory.id, "indexed", indexed=True)
      return True
    except Exception as exc:
      logger.error("Failed to index memory %s: %s", memory.id, exc)
      self.repo.mark_index_status(memory.id, "pending")
      return False

  def _recency_score(self, source_date: Optional[date], half_life_days: int = 30) -> float:
    if not source_date:
      return 0.5
    return math.exp(-0.693 * max(0, (date.today() - source_date).days) / half_life_days)

  def _frequency_score(self, access_count: int) -> float:
    return math.log(access_count + 1) / math.log(100)

  def _composite_score(self, semantic: float, importance: float, recency: float, frequency: float, lexical: float = 0.0) -> float:
    return semantic * 0.35 + lexical * 0.15 + importance * 0.25 + recency * 0.15 + min(frequency, 1.0) * 0.10

  def retrieve(self, query: str, top_k: int = 5) -> list[Memory]:
    if not query.strip():
      return self.repo.get_all(status="active")[:top_k]
    candidates: dict[int, tuple[Memory, float, float]] = {}
    for memory in self.repo.search_text(query, limit=max(top_k * 4, 20)):
      candidates[memory.id] = (memory, 0.0, 1.0)
    if self._collection is not None:
      try:
        results = self._collection.query(query_embeddings=[self.embedder.embed(query)], n_results=min(top_k * 5, 30))
        for index, mem_id in enumerate((results.get("ids") or [[]])[0]):
          memory = self.repo.get_by_id(int(mem_id))
          if memory and memory.status == "active":
            distance = (results.get("distances") or [[0.5]])[0][index]
            semantic = max(0.0, 1.0 - float(distance))
            old = candidates.get(memory.id)
            candidates[memory.id] = (memory, max(semantic, old[1] if old else 0.0), old[2] if old else 0.0)
      except Exception as exc:
        logger.error("Chroma query failed: %s", exc)
    if not candidates:
      for memory in self.repo.get_all(status="active")[: max(top_k * 4, 20)]:
        candidates[memory.id] = (memory, self.embedder.similarity(query, memory.text), 0.0)
    ranked = sorted(
      ((memory, self._composite_score(semantic, memory.importance, self._recency_score(memory.source_date), self._frequency_score(memory.access_count), lexical))
       for memory, semantic, lexical in candidates.values()), key=lambda item: item[1], reverse=True,
    )
    selected: list[Memory] = []
    for memory, score in ranked:
      if score < 0.08:
        continue
      # Simple MMR-style diversity: do not return near-duplicate text snippets.
      if any(self.embedder.similarity(memory.text, chosen.text) > 0.94 for chosen in selected):
        continue
      self.repo.increment_access(memory.id)
      selected.append(self.repo.get_by_id(memory.id) or memory)
      if len(selected) == top_k:
        break
    return selected

  def update(self, memory_id: int, **changes) -> Optional[Memory]:
    memory = self.repo.update(memory_id, **changes)
    if memory and ("text" in changes or "status" in changes):
      self._upsert_fts(memory)
      if memory.status == "active":
        self._index_memory(memory)
      elif self._collection is not None:
        try:
          self._collection.delete(ids=[str(memory.id)])
          self.repo.mark_index_status(memory.id, "removed")
        except Exception:
          self.repo.mark_index_status(memory.id, "pending")
    return memory

  def delete(self, memory_id: int) -> bool:
    if self._collection is not None:
      try:
        self._collection.delete(ids=[str(memory_id)])
      except Exception as exc:
        logger.warning("Could not remove vector %s: %s", memory_id, exc)
    from database.connection import get_db
    with get_db() as conn:
      conn.execute("DELETE FROM memory_fts WHERE memory_id = ?", (memory_id,))
    return self.repo.delete(memory_id)

  def reconcile_index(self) -> dict[str, int]:
    """Repair all active vectors and remove vectors for archived/deleted SQLite rows."""
    active = self.repo.get_all(status="active")
    indexed = 0
    for memory in active:
      indexed += int(self._index_memory(memory))
    removed = 0
    if self._collection is not None:
      try:
        vector_ids = set((self._collection.get(include=[]).get("ids") or []))
        desired = {str(memory.id) for memory in active}
        stale = list(vector_ids - desired)
        if stale:
          self._collection.delete(ids=stale)
          removed = len(stale)
      except Exception as exc:
        logger.warning("Could not reconcile stale vectors: %s", exc)
    return {"indexed": indexed, "removed": removed, "active": len(active)}

  def get_commitments(self, pending_only: bool = True) -> list[Memory]:
    return self.repo.get_commitments(pending_only=pending_only)

  def count(self) -> int:
    return self.repo.count(status="active")
