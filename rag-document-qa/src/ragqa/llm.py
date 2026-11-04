"""LLM abstraction. Swap providers without touching the pipeline."""
from __future__ import annotations

import os
import re
from typing import Protocol


class LLM(Protocol):
    def generate(self, system: str, prompt: str) -> str: ...


class AnthropicLLM:
    """Claude via the official SDK (``pip install anthropic``, set ANTHROPIC_API_KEY)."""

    def __init__(self, model: str | None = None, max_tokens: int = 700) -> None:
        import anthropic  # imported lazily so the package works offline

        self._client = anthropic.Anthropic()
        self._model = model or os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")
        self._max_tokens = max_tokens

    def generate(self, system: str, prompt: str) -> str:
        msg = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in msg.content if block.type == "text").strip()


class ExtractiveLLM:
    """Offline stand-in: returns the first context passage verbatim with its citation.

    Useful for demos, CI and tests: no network, no cost, fully deterministic.
    """

    def generate(self, system: str, prompt: str) -> str:
        match = re.search(r"\[(\d+)\]\s*\(.*?\)\s*(.+?)(?:\n\n|\Z)", prompt, flags=re.S)
        if not match:
            return "I could not find this in the provided documents."
        return f"{match.group(2).strip()} [{match.group(1)}]"
