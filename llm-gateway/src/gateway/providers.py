"""Provider interface plus a Claude implementation and a configurable mock."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable, Protocol

from .errors import ProviderError


@dataclass(frozen=True)
class Completion:
    text: str
    input_tokens: int
    output_tokens: int
    model: str


class Provider(Protocol):
    name: str

    def complete(self, prompt: str, max_tokens: int) -> Completion: ...


class MockProvider:
    """Deterministic provider for tests and demos. Can fail on purpose to exercise resilience."""

    def __init__(self, name: str = "mock", model: str = "mock-small", fail_times: int = 0,
                 retryable: bool = True, always_fail: bool = False,
                 reply: Callable[[str], str] = lambda p: f"echo: {p}") -> None:
        self.name, self.model = name, model
        self.fail_times, self.retryable, self.always_fail, self._reply = fail_times, retryable, always_fail, reply
        self.calls = 0

    def complete(self, prompt: str, max_tokens: int) -> Completion:
        self.calls += 1
        if self.always_fail or self.calls <= self.fail_times:
            raise ProviderError(f"{self.name} unavailable", retryable=self.retryable)
        text = self._reply(prompt)
        return Completion(text, input_tokens=max(1, len(prompt) // 4), output_tokens=max(1, len(text) // 4), model=self.model)


class AnthropicProvider:
    """Claude via the official SDK, with SDK errors mapped to retryable / non-retryable."""

    name = "anthropic"

    def __init__(self, model: str | None = None) -> None:
        import anthropic

        self._anthropic = anthropic
        self._client = anthropic.Anthropic(max_retries=0)  # the gateway owns retry policy
        self.model = model or os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")

    def complete(self, prompt: str, max_tokens: int) -> Completion:
        a = self._anthropic
        try:
            msg = self._client.messages.create(model=self.model, max_tokens=max_tokens,
                                               messages=[{"role": "user", "content": prompt}])
        except a.RateLimitError as exc:
            raise ProviderError(f"rate limited upstream: {exc}", retryable=True) from exc
        except a.APIStatusError as exc:
            raise ProviderError(f"upstream status {exc.status_code}", retryable=exc.status_code >= 500) from exc
        except a.APIConnectionError as exc:  # includes timeouts
            raise ProviderError(f"connection error: {exc}", retryable=True) from exc
        text = "".join(b.text for b in msg.content if b.type == "text")
        return Completion(text, msg.usage.input_tokens, msg.usage.output_tokens, self.model)
