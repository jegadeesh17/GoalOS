"""Memory and embedding service tests."""

from datetime import date

from services.embedding_service import EmbeddingService
from services.memory_service import MemoryService


class TestEmbeddingService:
  def test_embed_returns_vector(self):
    svc = EmbeddingService()
    vec = svc.embed("Hello world")
    assert isinstance(vec, list)
    assert len(vec) > 0

  def test_cache_hit(self):
    svc = EmbeddingService()
    v1 = svc.embed("cached text")
    v2 = svc.embed("cached text")
    assert v1 == v2

  def test_similarity_same_text(self):
    svc = EmbeddingService()
    sim = svc.similarity("python coding", "python coding")
    assert sim > 0.9

  def test_empty_text(self):
    svc = EmbeddingService()
    vec = svc.embed("")
    assert len(vec) > 0


class TestMemoryService:
  def test_store_and_retrieve(self, temp_db):
    svc = MemoryService()
    svc.store("Focus on what matters most", "lesson", importance=0.8, source_date=date.today())
    svc.store("Grateful for supportive parents", "achievement", importance=0.3)
    results = svc.retrieve("focus matters", top_k=2)
    assert len(results) >= 1

  def test_retrieve_empty_query(self, temp_db):
    svc = MemoryService()
    svc.store("Test memory", "lesson")
    results = svc.retrieve("", top_k=5)
    assert len(results) >= 1

  def test_commitments(self, temp_db):
    svc = MemoryService()
    svc.store("I will run tomorrow morning", "commitment", importance=0.7)
    commitments = svc.get_commitments()
    assert len(commitments) >= 1

  def test_count(self, temp_db):
    svc = MemoryService()
    svc.store("Memory one", "lesson")
    svc.store("Memory two", "achievement")
    assert svc.count() == 2
