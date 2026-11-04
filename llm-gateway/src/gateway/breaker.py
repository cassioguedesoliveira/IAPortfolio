"""Circuit breaker: stop hammering a provider that is clearly down, and probe it again later."""
from __future__ import annotations

import time
from typing import Callable


class CircuitBreaker:
    CLOSED, OPEN, HALF_OPEN = "closed", "open", "half_open"

    def __init__(self, failure_threshold: int = 3, cooldown: float = 30.0,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self.failure_threshold, self.cooldown, self._clock = failure_threshold, cooldown, clock
        self.state = self.CLOSED
        self._failures = 0
        self._opened_at = 0.0

    def allow(self) -> bool:
        if self.state == self.OPEN:
            if self._clock() - self._opened_at >= self.cooldown:
                self.state = self.HALF_OPEN  # let one trial request through
                return True
            return False
        return True

    def record_success(self) -> None:
        self.state, self._failures = self.CLOSED, 0

    def record_failure(self) -> None:
        self._failures += 1
        if self.state == self.HALF_OPEN or self._failures >= self.failure_threshold:
            self.state, self._opened_at = self.OPEN, self._clock()
