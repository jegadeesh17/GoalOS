"""Production-grade Rate Limiter for OpenRouter Free Tier."""

import logging
import random
import time
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)
T = TypeVar("T")


class RateLimiter:
  """Leaky-bucket rate limiter with exponential backoff & jitter for free API tiers."""

  def __init__(self, requests_per_minute: float = 14.0, max_retries: int = 4, base_backoff: float = 5.0):
    self.min_interval = 60.0 / max(1.0, requests_per_minute)
    self.last_call_time = 0.0
    self.max_retries = max_retries
    self.base_backoff = base_backoff

  def wait_if_needed(self) -> None:
    """Enforce minimum interval between consecutive API requests."""
    now = time.time()
    elapsed = now - self.last_call_time
    if elapsed < self.min_interval:
      sleep_time = self.min_interval - elapsed
      logger.debug(f"[RateLimiter] Throttling for {sleep_time:.2f}s to respect free-tier RPM...")
      time.sleep(sleep_time)
    self.last_call_time = time.time()

  def execute_with_retry(self, func: Callable[[], T], operation_name: str = "LLM Call") -> tuple[T, float]:
    """Execute callable with rate-limiting, timing, and automatic 429/503 retry."""
    for attempt in range(1, self.max_retries + 1):
      self.wait_if_needed()
      start_t = time.perf_counter()
      try:
        result = func()
        latency = time.perf_counter() - start_t

        # Check if the result dictionary indicates rate limit or server error
        if isinstance(result, dict) and result.get("error") in ("rate_limit", "api_error", "http_429", "http_503"):
          err_msg = result.get("error_detail", "") or result.get("error", "")
          if "429" in err_msg or "rate" in err_msg.lower() or "limit" in err_msg.lower() or "503" in err_msg:
            if attempt < self.max_retries:
              backoff = (self.base_backoff * (2 ** (attempt - 1))) + random.uniform(0.5, 2.5)
              logger.warning(f"[{operation_name}] Rate limited (attempt {attempt}/{self.max_retries}). Backing off for {backoff:.1f}s...")
              time.sleep(backoff)
              continue

        return result, latency

      except Exception as e:
        latency = time.perf_counter() - start_t
        err_str = str(e)
        if ("429" in err_str or "rate limit" in err_str.lower() or "503" in err_str) and attempt < self.max_retries:
          backoff = (self.base_backoff * (2 ** (attempt - 1))) + random.uniform(0.5, 2.5)
          logger.warning(f"[{operation_name}] Exception {e}. Retrying in {backoff:.1f}s (attempt {attempt}/{self.max_retries})...")
          time.sleep(backoff)
        else:
          logger.error(f"[{operation_name}] Failed on attempt {attempt}: {e}")
          if attempt == self.max_retries:
            raise e

    raise RuntimeError(f"[{operation_name}] Exceeded maximum retries ({self.max_retries})")
