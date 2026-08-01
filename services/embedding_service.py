"""Text embedding service with in-memory caching."""

import hashlib
import logging

import numpy as np

logger = logging.getLogger(__name__)

_MODEL = None
_CACHE: dict[str, list[float]] = {}


def _get_model():
  global _MODEL
  if _MODEL is None:
    try:
      from sentence_transformers import SentenceTransformer
      _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    except Exception as e:
      logger.warning("Could not load sentence-transformers: %s. Using fallback.", e)
      _MODEL = "fallback"
  return _MODEL


def _fallback_embed(text: str) -> list[float]:
  """Simple hash-based fallback embedding for tests/offline."""
  h = hashlib.md5(text.encode()).digest()
  return [b / 255.0 for b in h] * 24  # 384-dim approx


class EmbeddingService:
  """Embed text with caching."""

  def __init__(self):
    self._cache = _CACHE

  def embed(self, text: str) -> list[float]:
    """Return embedding vector, using cache on subsequent calls."""
    if not text:
      return _fallback_embed("")
    key = hashlib.sha256(text.encode()).hexdigest()
    if key in self._cache:
      return self._cache[key]
    model = _get_model()
    if model == "fallback":
      vector = _fallback_embed(text)
    else:
      vector = model.encode(text).tolist()
    self._cache[key] = vector
    return vector

  def similarity(self, text_a: str, text_b: str) -> float:
    """Cosine similarity between two texts (0-1)."""
    vec_a = np.array(self.embed(text_a))
    vec_b = np.array(self.embed(text_b))
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
      return 0.0
    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))

  def clear_cache(self) -> None:
    self._cache.clear()
