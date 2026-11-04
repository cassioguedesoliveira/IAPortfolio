"""Cost accounting. Prices are USD per 1M tokens and MUST be configured from your provider's price list."""
from __future__ import annotations

# Illustrative placeholders only. Replace with real prices for the models you use.
DEFAULT_PRICES: dict[str, tuple[float, float]] = {
    "mock-small": (1.0, 3.0),
    "mock-large": (5.0, 15.0),
}


def cost_usd(prices: dict[str, tuple[float, float]], model: str, input_tokens: int, output_tokens: int) -> float:
    if model not in prices:
        return 0.0  # unknown model: do not guess, but make it visible via metrics.unpriced
    price_in, price_out = prices[model]
    return (input_tokens * price_in + output_tokens * price_out) / 1_000_000
