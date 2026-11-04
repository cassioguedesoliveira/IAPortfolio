"""Per-key token-bucket rate limiting."""
from __future__ import annotations

import threading
import time
from typing import Callable

from .errors import RateLimitExceeded


class TokenBucket:
    def __init__(self, rate: float, capacity: float, clock: Callable[[], float] = time.monotonic) -> None:
        self.rate, self.capacity, self._clock = rate, capacity, clock
        self._tokens, self._updated = capacity, clock()

    def try_acquire(self, n: float = 1.0) -> float:
        """Return 0.0 if ``n`` tokens were taken, otherwise the seconds to wait."""
        now = self._clock()
        self._tokens = min(self.capacity, self._tokens + (now - self._updated) * self.rate)
        self._updated = now
        if self._tokens >= n:
            self._tokens -= n
            return 0.0
        return (n - self._tokens) / self.rate


class RateLimiter:
    """One bucket per API key, so a noisy client cannot starve the others."""

    def __init__(self, rate: float = 5.0, burst: float = 10.0, clock: Callable[[], float] = time.monotonic) -> None:
        self.rate, self.burst, self._clock = rate, burst, clock
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = threading.Lock()

    def check(self, key: str) -> None:
        with self._lock:
            bucket = self._buckets.setdefault(key, TokenBucket(self.rate, self.burst, self._clock))
            wait = bucket.try_acquire()
        if wait > 0:
            raise RateLimitExceeded(wait)
