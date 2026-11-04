"""Guardrails that sit *outside* the model, so they cannot be talked around."""
from __future__ import annotations

import re
from dataclasses import dataclass

from .types import ToolCall

_PATTERNS = [
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("CPF", re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")),
    ("CARD", re.compile(r"\b(?:\d[ -]?){13,16}\b")),
    ("PHONE", re.compile(r"(?<!\w)(?:\+?\d{1,3}[ -]?)?\(?\d{2}\)?[ -]?\d{4,5}-?\d{4}\b")),
]


def redact_pii(text: str) -> str:
    """Replace emails, CPF, card numbers and phone numbers before text reaches the model."""
    for label, pattern in _PATTERNS:
        text = pattern.sub(f"[{label}]", text)
    return text


@dataclass
class Policy:
    """Business rules enforced in code. Returns a reason string when a call must be blocked."""

    max_auto_refund: float = 100.0

    def check(self, call: ToolCall) -> str | None:
        if call.name == "issue_refund":
            amount = call.arguments.get("amount")
            if isinstance(amount, (int, float)) and amount > self.max_auto_refund:
                return (f"refund of {amount:.2f} exceeds the automatic limit of "
                        f"{self.max_auto_refund:.2f}; a human agent must approve it")
        return None
