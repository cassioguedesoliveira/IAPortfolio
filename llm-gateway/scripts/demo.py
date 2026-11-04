"""Offline demo of resilience: retries, fallback, circuit breaker and caching.

Run: PYTHONPATH=src python scripts/demo.py
"""
from gateway import Gateway
from gateway.providers import MockProvider

flaky_primary = MockProvider("primary", fail_times=2)         # succeeds on the 3rd attempt
dead_primary = MockProvider("dead-primary", always_fail=True)
backup = MockProvider("backup", model="mock-large")

print("1) transient failures are retried")
gw = Gateway([flaky_primary], sleep=lambda s: None)
r = gw.complete("client-a", "hello")
print(f"   provider={r.provider} attempts={r.attempts}")

print("2) a dead provider triggers fallback")
gw = Gateway([dead_primary, backup], sleep=lambda s: None)
r = gw.complete("client-a", "hello")
print(f"   provider={r.provider} cost=${r.cost_usd:.8f}")

print("3) identical request is served from cache at zero cost")
r = gw.complete("client-a", "hello")
print(f"   cached={r.cached} cost=${r.cost_usd}")

print("4) metrics")
print("  ", gw.metrics.snapshot())
