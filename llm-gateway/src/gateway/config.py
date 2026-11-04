"""Build a Gateway from environment variables.

PROVIDERS=anthropic,mock   (ordered: first is primary)
RATE_PER_SEC=5  RATE_BURST=10  CACHE_TTL=300
"""
from __future__ import annotations

import os

from .cache import TTLCache
from .gateway import Gateway
from .providers import AnthropicProvider, MockProvider
from .ratelimit import RateLimiter


def build_gateway() -> Gateway:
    names = [n.strip() for n in os.environ.get("PROVIDERS", "mock").split(",") if n.strip()]
    providers = [AnthropicProvider() if n == "anthropic" else MockProvider(name=n) for n in names]
    return Gateway(
        providers,
        cache=TTLCache(ttl=float(os.environ.get("CACHE_TTL", "300"))),
        limiter=RateLimiter(float(os.environ.get("RATE_PER_SEC", "5")), float(os.environ.get("RATE_BURST", "10"))),
    )
