from __future__ import annotations

import threading
from collections import Counter


class Metrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.counters: Counter[str] = Counter()
        self.cost_usd = 0.0
        self.saved_usd = 0.0
        self._latencies_ms: list[float] = []

    def incr(self, name: str, n: int = 1) -> None:
        with self._lock:
            self.counters[name] += n

    def add_cost(self, usd: float) -> None:
        with self._lock:
            self.cost_usd += usd

    def add_saved(self, usd: float) -> None:
        with self._lock:
            self.saved_usd += usd

    def observe_latency(self, ms: float) -> None:
        with self._lock:
            self._latencies_ms.append(ms)
            del self._latencies_ms[:-5000]  # bounded memory

    def snapshot(self) -> dict:
        with self._lock:
            lat = sorted(self._latencies_ms)
            req, hits = self.counters["requests"], self.counters["cache_hits"]
            return {
                "counters": dict(self.counters),
                "cache_hit_rate": hits / req if req else 0.0,
                "cost_usd": round(self.cost_usd, 6),
                "saved_usd_by_cache": round(self.saved_usd, 6),
                "latency_ms": {"p50": lat[len(lat) // 2], "p95": lat[min(len(lat) - 1, int(len(lat) * 0.95))]} if lat else {},
            }
