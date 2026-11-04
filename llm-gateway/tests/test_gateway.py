import unittest

from gateway import AllProvidersFailed, Gateway, ProviderError, RateLimitExceeded
from gateway.breaker import CircuitBreaker
from gateway.cache import TTLCache
from gateway.providers import MockProvider
from gateway.ratelimit import RateLimiter, TokenBucket
from gateway.retry import retry_call


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class CacheTests(unittest.TestCase):
    def test_ttl_expiry(self):
        clock = FakeClock()
        cache = TTLCache(ttl=10, clock=clock)
        cache.set("k", "v")
        self.assertEqual(cache.get("k"), "v")
        clock.advance(10)
        self.assertIsNone(cache.get("k"))

    def test_lru_eviction_respects_recent_use(self):
        cache = TTLCache(max_size=2, ttl=100)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.get("a")  # a is now more recent than b
        cache.set("c", 3)
        self.assertIsNone(cache.get("b"))
        self.assertEqual(cache.get("a"), 1)


class RateLimitTests(unittest.TestCase):
    def test_bucket_refills_over_time(self):
        clock = FakeClock()
        bucket = TokenBucket(rate=1, capacity=2, clock=clock)
        self.assertEqual(bucket.try_acquire(), 0.0)
        self.assertEqual(bucket.try_acquire(), 0.0)
        self.assertAlmostEqual(bucket.try_acquire(), 1.0)
        clock.advance(1)
        self.assertEqual(bucket.try_acquire(), 0.0)

    def test_keys_are_isolated(self):
        limiter = RateLimiter(rate=1, burst=1, clock=FakeClock())
        limiter.check("a")
        with self.assertRaises(RateLimitExceeded):
            limiter.check("a")
        limiter.check("b")  # other client unaffected


class RetryTests(unittest.TestCase):
    def test_backoff_grows_and_succeeds(self):
        calls, delays = {"n": 0}, []

        def flaky():
            calls["n"] += 1
            if calls["n"] < 3:
                raise ProviderError("boom")
            return "ok"

        result, attempts = retry_call(flaky, attempts=3, base_delay=1.0, sleep=delays.append, rng=lambda: 1.0)
        self.assertEqual((result, attempts), ("ok", 3))
        self.assertEqual(delays, [1.0, 2.0])

    def test_non_retryable_fails_immediately(self):
        calls = {"n": 0}

        def bad():
            calls["n"] += 1
            raise ProviderError("invalid key", retryable=False)

        with self.assertRaises(ProviderError):
            retry_call(bad, attempts=5, sleep=lambda s: None)
        self.assertEqual(calls["n"], 1)


class BreakerTests(unittest.TestCase):
    def test_opens_then_half_open_then_closes(self):
        clock = FakeClock()
        breaker = CircuitBreaker(failure_threshold=2, cooldown=30, clock=clock)
        breaker.record_failure()
        breaker.record_failure()
        self.assertFalse(breaker.allow())
        clock.advance(30)
        self.assertTrue(breaker.allow())
        self.assertEqual(breaker.state, "half_open")
        breaker.record_success()
        self.assertEqual(breaker.state, "closed")

    def test_failed_probe_reopens(self):
        clock = FakeClock()
        breaker = CircuitBreaker(failure_threshold=1, cooldown=10, clock=clock)
        breaker.record_failure()
        clock.advance(10)
        breaker.allow()
        breaker.record_failure()
        self.assertFalse(breaker.allow())


def gw(providers, **kw):
    return Gateway(providers, sleep=lambda s: None, **kw)


class GatewayTests(unittest.TestCase):
    def test_cache_hit_costs_nothing_and_skips_provider(self):
        p = MockProvider()
        g = gw([p])
        first = g.complete("k", "hello world")
        second = g.complete("k", "hello world")
        self.assertFalse(first.cached)
        self.assertTrue(second.cached)
        self.assertEqual((second.cost_usd, p.calls), (0.0, 1))
        snap = g.metrics.snapshot()
        self.assertAlmostEqual(snap["cache_hit_rate"], 0.5)
        self.assertGreater(snap["saved_usd_by_cache"], 0)

    def test_different_max_tokens_is_a_different_cache_entry(self):
        p = MockProvider()
        g = gw([p])
        g.complete("k", "hi", max_tokens=10)
        g.complete("k", "hi", max_tokens=20)
        self.assertEqual(p.calls, 2)

    def test_retries_then_succeeds_on_same_provider(self):
        g = gw([MockProvider("p", fail_times=2)])
        r = g.complete("k", "hi")
        self.assertEqual((r.provider, r.attempts), ("p", 3))

    def test_falls_back_when_primary_is_down(self):
        g = gw([MockProvider("primary", always_fail=True), MockProvider("backup")])
        r = g.complete("k", "hi")
        self.assertEqual(r.provider, "backup")
        self.assertEqual(g.metrics.counters["fallbacks"], 1)

    def test_non_retryable_error_still_falls_back_without_retrying(self):
        primary = MockProvider("primary", always_fail=True, retryable=False)
        g = gw([primary, MockProvider("backup")])
        g.complete("k", "hi")
        self.assertEqual(primary.calls, 1)

    def test_all_providers_failing_raises_with_details(self):
        g = gw([MockProvider("a", always_fail=True), MockProvider("b", always_fail=True)])
        with self.assertRaises(AllProvidersFailed) as ctx:
            g.complete("k", "hi")
        self.assertEqual(set(ctx.exception.failures), {"a", "b"})

    def test_breaker_skips_provider_after_repeated_failures(self):
        clock = FakeClock()
        primary = MockProvider("primary", always_fail=True)
        g = gw([primary, MockProvider("backup")], retry_attempts=1,
               breaker_factory=lambda: CircuitBreaker(failure_threshold=2, cooldown=60, clock=clock))
        for i in range(4):
            g.complete("k", f"prompt {i}")
        self.assertEqual(primary.calls, 2)  # calls 3 and 4 were short-circuited
        self.assertEqual(g.metrics.counters["circuit_skips"], 2)

    def test_rate_limit_applies_per_key(self):
        g = gw([MockProvider()], limiter=RateLimiter(rate=1, burst=1, clock=FakeClock()))
        g.complete("a", "one")
        with self.assertRaises(RateLimitExceeded):
            g.complete("a", "two")
        g.complete("b", "three")

    def test_cost_is_computed_from_token_usage(self):
        g = gw([MockProvider(model="mock-large", reply=lambda p: "x" * 400)])
        r = g.complete("k", "y" * 400)  # 100 input tokens, 100 output tokens
        self.assertAlmostEqual(r.cost_usd, (100 * 5.0 + 100 * 15.0) / 1e6)

    def test_unpriced_models_are_flagged_not_guessed(self):
        g = gw([MockProvider(model="unknown-model")])
        self.assertEqual(g.complete("k", "hi").cost_usd, 0.0)
        self.assertEqual(g.metrics.counters["unpriced_responses"], 1)

    def test_input_validation(self):
        g = gw([MockProvider()])
        with self.assertRaises(ValueError):
            g.complete("k", "   ")
        with self.assertRaises(ValueError):
            g.complete("k", "hi", max_tokens=0)


if __name__ == "__main__":
    unittest.main()
