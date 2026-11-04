"""Thread-safe LRU cache with per-entry TTL and an injectable clock (so tests need no sleeping)."""
from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Any, Callable


class TTLCache:
    def __init__(self, max_size: int = 1000, ttl: float = 300.0, clock: Callable[[], float] = time.monotonic) -> None:
        if max_size <= 0 or ttl <= 0:
            raise ValueError("max_size and ttl must be positive")
        self.max_size, self.ttl, self._clock = max_size, ttl, clock
        self._data: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            expires_at, value = item
            if self._clock() >= expires_at:
                del self._data[key]
                return None
            self._data.move_to_end(key)  # mark as recently used
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._data[key] = (self._clock() + self.ttl, value)
            self._data.move_to_end(key)
            while len(self._data) > self.max_size:
                self._data.popitem(last=False)  # evict least recently used

    def __len__(self) -> int:
        return len(self._data)
