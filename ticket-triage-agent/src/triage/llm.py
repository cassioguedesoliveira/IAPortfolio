"""LLM adapters: a real tool-calling model, plus deterministic stand-ins for tests and demos."""
from __future__ import annotations

import json
import os
import re
from typing import Protocol

from .types import Message, Reply, ToolCall


class LLM(Protocol):
    def next(self, system: str, messages: list[Message], tool_specs: list[dict]) -> Reply: ...


class ScriptedLLM:
    """Replays a fixed list of replies. Records what it was shown (used to assert on PII redaction)."""

    def __init__(self, replies: list[Reply]) -> None:
        self._replies = list(replies)
        self.seen: list[list[Message]] = []

    def next(self, system, messages, tool_specs):
        self.seen.append(list(messages))
        return self._replies.pop(0) if self._replies else Reply(tool_calls=[ToolCall("x", "search_kb", {"query": "loop"})])


class PolicyLLM:
    """Deterministic rule-based 'model' so the demo runs offline. NOT intelligent; it mimics tool use."""

    def next(self, system, messages, tool_specs):
        ticket = messages[0].content
        tool_msgs = [m for m in messages if m.role == "tool"]
        order_match = re.search(r"ORD-\d+", ticket)
        wants_refund = bool(re.search(r"refund|money back|reembolso", ticket, re.I))

        if not tool_msgs:
            if order_match:
                return Reply(tool_calls=[ToolCall("c1", "get_order", {"order_id": order_match.group(0)})])
            return Reply(tool_calls=[ToolCall("c1", "search_kb", {"query": ticket})])

        last = tool_msgs[-1].content
        if last.startswith("BLOCKED"):
            return self._final("billing", "high", "Your refund needs approval from a specialist; we will contact you shortly.", True)
        if last.startswith("{") and wants_refund and len(tool_msgs) == 1:
            order = json.loads(last)
            return Reply(tool_calls=[ToolCall("c2", "issue_refund", {"order_id": order["order_id"], "amount": order["total"]})])
        if last.startswith("refund of"):
            return self._final("billing", "normal", f"Done: {last}. It will reach you in 5 business days.", False)
        if last.startswith("ERROR"):
            return self._final("billing", "normal", f"We could not complete the refund automatically ({last[7:]}).", True)
        return self._final("shipping" if order_match else "other", "normal",
                           "Here is what we found: " + last.replace("\n", " ")[:200], False)

    @staticmethod
    def _final(category, priority, reply, needs_human):
        return Reply(text=json.dumps({"category": category, "priority": priority, "reply": reply,
                                      "needs_human": needs_human}))


class AnthropicToolLLM:
    """Claude with native tool use (``pip install anthropic``; set ANTHROPIC_API_KEY)."""

    def __init__(self, model: str | None = None, max_tokens: int = 1024) -> None:
        import anthropic

        self._client = anthropic.Anthropic()
        self._model = model or os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")
        self._max_tokens = max_tokens

    def next(self, system, messages, tool_specs):
        resp = self._client.messages.create(
            model=self._model, max_tokens=self._max_tokens, system=system,
            tools=tool_specs, messages=self.convert(messages),
        )
        text = "".join(b.text for b in resp.content if b.type == "text")
        calls = [ToolCall(b.id, b.name, dict(b.input)) for b in resp.content if b.type == "tool_use"]
        return Reply(text=text, tool_calls=calls)

    @staticmethod
    def convert(messages: list[Message]) -> list[dict]:
        """Map our neutral messages to the Anthropic Messages API format."""
        out: list[dict] = []
        for m in messages:
            if m.role == "user":
                out.append({"role": "user", "content": m.content})
            elif m.role == "assistant":
                blocks: list[dict] = [{"type": "text", "text": m.content}] if m.content else []
                blocks += [{"type": "tool_use", "id": c.id, "name": c.name, "input": c.arguments} for c in m.tool_calls]
                out.append({"role": "assistant", "content": blocks})
            else:  # tool result: consecutive results must share one user message
                block = {"type": "tool_result", "tool_use_id": m.tool_call_id, "content": m.content}
                last = out[-1] if out else None
                if last and last["role"] == "user" and isinstance(last["content"], list):
                    last["content"].append(block)
                else:
                    out.append({"role": "user", "content": [block]})
        return out
