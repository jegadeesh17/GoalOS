"""Memory service with ChromaDB and composite retrieval."""

import logging
import math
from datetime import date, datetime
from typing import Optional

from database.repositories.memory_repository import MemoryRepository
from models.memory import Memory, MemoryCreate
from services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

_COLLECTION = None


def _get_collection(chroma_path: str):
  global _COLLECTION
  if _COLLECTION is not None:
    return _COLLECTION
  try:
    import chromadb
    client = chromadb.PersistentClient(path=chroma_path)
    _COLLECTION = client.get_or_create_collection(
      name="goalos_memories",
      metadata={"hnsw:space": "cosine"},
    )
  except Exception as e:
    logger.warning("ChromaDB unavailable: %s", e)
    _COLLECTION = None
  return _COLLECTION


class MemoryService:
  """Store and retrieve memories with semantic search."""

  def __init__(self, chroma_path: Optional[str] = None):
    from config.settings import settings
    self.chroma_path = chroma_path or settings.CHROMA_PATH
    self.repo = MemoryRepository()
    self.embedder = EmbeddingService()
    self._collection = _get_collection(self.chroma_path)

  def store(
    self,
    text: str,
    memory_type: str,
    importance: float = 0.5,
    source_date: Optional[date] = None,
    source_type: Optional[str] = None,
    source_id: Optional[int] = None,
  ) -> Memory:
    """Store memory in SQLite and ChromaDB."""
    memory = self.repo.create(MemoryCreate(
      text=text,
      type=memory_type,
      importance=importance,
      source_date=source_date,
      source_type=source_type,
      source_id=source_id,
    ))
    if self._collection is not None:
      try:
        embedding = self.embedder.embed(text)
        self._collection.upsert(
          ids=[str(memory.id)],
          embeddings=[embedding],
          documents=[text],
          metadatas=[{
            "type": memory_type,
            "importance": importance,
            "source_date": source_date.isoformat() if source_date else "",
          }],
        )
      except Exception as e:
        logger.error("Failed to store embedding: %s", e)
    return memory

  def _recency_score(self, source_date: Optional[date], half_life_days: int = 30) -> float:
    if not source_date:
      return 0.5
    days_ago = (date.today() - source_date).days
    return math.exp(-0.693 * days_ago / half_life_days)

  def _frequency_score(self, access_count: int) -> float:
    return math.log(access_count + 1) / math.log(100)

  def _composite_score(
    self,
    semantic: float,
    importance: float,
    recency: float,
    frequency: float,
  ) -> float:
    return (
      semantic * 0.40
      + importance * 0.30
      + recency * 0.20
      + min(frequency, 1.0) * 0.10
    )

  def retrieve(self, query: str, top_k: int = 5) -> list[Memory]:
    """Retrieve memories ranked by composite score."""
    if not query:
      memories = self.repo.get_all()
      return memories[:top_k]

    candidates: list[tuple[Memory, float]] = []

    if self._collection is not None:
      try:
        query_embedding = self.embedder.embed(query)
        results = self._collection.query(
          query_embeddings=[query_embedding],
          n_results=min(top_k * 3, 20),
        )
        if results and results["ids"] and results["ids"][0]:
          for i, mem_id in enumerate(results["ids"][0]):
            memory = self.repo.get_by_id(int(mem_id))
            if memory:
              distance = results["distances"][0][i] if results.get("distances") else 0.5
              semantic = max(0.0, 1.0 - distance)
              recency = self._recency_score(memory.source_date)
              freq = self._frequency_score(memory.access_count)
              composite = self._composite_score(semantic, memory.importance, recency, freq)
              candidates.append((memory, composite))
      except Exception as e:
        logger.error("ChromaDB query failed: %s", e)

    if not candidates:
      for memory in self.repo.search_text(query, limit=top_k * 2):
        semantic = self.embedder.similarity(query, memory.text)
        recency = self._recency_score(memory.source_date)
        freq = self._frequency_score(memory.access_count)
        composite = self._composite_score(semantic, memory.importance, recency, freq)
        candidates.append((memory, composite))

    candidates.sort(key=lambda x: x[1], reverse=True)
    results = []
    for memory, _ in candidates[:top_k]:
      self.repo.increment_access(memory.id)
      results.append(self.repo.get_by_id(memory.id))
    return [m for m in results if m is not None]

  def get_commitments(self, pending_only: bool = True) -> list[Memory]:
    return self.repo.get_commitments(pending_only=pending_only)

  def count(self) -> int:
    return self.repo.count()
