"""Retry with exponential backoff and jitter. Only retryable errors are retried."""
from __future__ import annotations

import random
import time
from typing import Callable, TypeVar

from .errors import ProviderError

T = TypeVar("T")


def retry_call(
    fn: Callable[[], T],
    attempts: int = 3,
    base_delay: float = 0.2,
    max_delay: float = 5.0,
    sleep: Callable[[float], None] = time.sleep,
    rng: Callable[[], float] = random.random,
) -> tuple[T, int]:
    """Call ``fn`` up to ``attempts`` times. Returns ``(result, attempts_used)``.

    Jitter (50-100% of the computed delay) prevents many clients from retrying in lockstep.
    """
    for attempt in range(1, attempts + 1):
        try:
            return fn(), attempt
        except ProviderError as exc:
            exc.attempts = attempt
            if not exc.retryable or attempt == attempts:
                raise
            delay = min(max_delay, base_delay * 2 ** (attempt - 1))
            sleep(delay * (0.5 + rng() / 2))
    raise AssertionError("unreachable")  # pragma: no cover
