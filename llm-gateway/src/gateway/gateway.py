"""Request flow: validate -> rate limit -> cache -> (breaker -> retry) per provider with fallback -> cost."""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Callable

from .breaker import CircuitBreaker
from .cache import TTLCache
from .errors import AllProvidersFailed, ProviderError
from .metrics import Metrics
from .pricing import DEFAULT_PRICES, cost_usd
from .providers import Completion, Provider
from .ratelimit import RateLimiter
from .retry import retry_call


@dataclass(frozen=True)
class GatewayResponse:
    text: str
    provider: str
    model: str
    cached: bool
    cost_usd: float
    attempts: int


class Gateway:
    def __init__(
        self,
        providers: list[Provider],
        cache: TTLCache | None = None,
        limiter: RateLimiter | None = None,
        prices: dict[str, tuple[float, float]] | None = None,
        retry_attempts: int = 3,
        sleep: Callable[[float], None] = time.sleep,
        breaker_factory: Callable[[], CircuitBreaker] = CircuitBreaker,
    ) -> None:
        if not providers:
            raise ValueError("at least one provider is required")
        self.providers = providers  # ordered by preference: first is primary, rest are fallbacks
        self.cache = cache or TTLCache()
        self.limiter = limiter or RateLimiter()
        self.prices = prices or DEFAULT_PRICES
        self.retry_attempts, self._sleep = retry_attempts, sleep
        self.breakers = {p.name: breaker_factory() for p in providers}
        self.metrics = Metrics()

    @staticmethod
    def _cache_key(prompt: str, max_tokens: int) -> str:
        return hashlib.sha256(json.dumps([prompt, max_tokens]).encode()).hexdigest()

    def complete(self, api_key: str, prompt: str, max_tokens: int = 256) -> GatewayResponse:
        if not prompt.strip():
            raise ValueError("prompt must not be empty")
        if not 1 <= max_tokens <= 4096:
            raise ValueError("max_tokens must be between 1 and 4096")

        self.metrics.incr("requests")
        try:
            self.limiter.check(api_key)
        except Exception:
            self.metrics.incr("rate_limited")
            raise

        key = self._cache_key(prompt, max_tokens)
        hit = self.cache.get(key)
        if hit is not None:
            completion, provider_name, original_cost = hit
            self.metrics.incr("cache_hits")
            self.metrics.add_saved(original_cost)
            return GatewayResponse(completion.text, provider_name, completion.model, True, 0.0, 0)

        start = time.perf_counter()
        failures: dict[str, str] = {}
        for index, provider in enumerate(self.providers):
            breaker = self.breakers[provider.name]
            if not breaker.allow():
                failures[provider.name] = "circuit open"
                self.metrics.incr("circuit_skips")
                continue
            try:
                completion, attempts = retry_call(lambda p=provider: p.complete(prompt, max_tokens),
                                                  attempts=self.retry_attempts, sleep=self._sleep)
            except ProviderError as exc:
                breaker.record_failure()
                failures[provider.name] = str(exc)
                self.metrics.incr("provider_failures")
                self.metrics.incr("retries", exc.attempts - 1)
                continue
            breaker.record_success()
            self.metrics.incr("retries", attempts - 1)
            if index > 0:
                self.metrics.incr("fallbacks")
            return self._finish(key, completion, provider.name, attempts, start)

        self.metrics.incr("all_failed")
        raise AllProvidersFailed(failures)

    def _finish(self, key: str, completion: Completion, provider_name: str, attempts: int, start: float) -> GatewayResponse:
        if completion.model not in self.prices:
            self.metrics.incr("unpriced_responses")
        cost = cost_usd(self.prices, completion.model, completion.input_tokens, completion.output_tokens)
        self.cache.set(key, (completion, provider_name, cost))
        self.metrics.add_cost(cost)
        self.metrics.observe_latency((time.perf_counter() - start) * 1000)
        return GatewayResponse(completion.text, provider_name, completion.model, False, cost, attempts)
