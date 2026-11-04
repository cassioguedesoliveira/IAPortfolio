"""Tool registry with strict argument validation.

Models produce malformed tool calls more often than people expect. We validate
every call against its JSON schema and return a readable error to the model so
it can self-correct, instead of crashing or executing with bad input.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


class ToolError(Exception):
    """A tool failed for a business reason (message is safe to show the model)."""


_TYPES = {"string": str, "number": (int, float), "integer": int, "boolean": bool}


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    input_schema: dict
    fn: Callable[..., str]


def validate_args(schema: dict, args: dict) -> None:
    props, required = schema.get("properties", {}), schema.get("required", [])
    for key in required:
        if key not in args:
            raise ToolError(f"missing required argument '{key}'")
    for key, value in args.items():
        if key not in props:
            raise ToolError(f"unexpected argument '{key}'")
        expected = _TYPES.get(props[key].get("type", "string"), object)
        if isinstance(value, bool) and props[key].get("type") != "boolean":
            raise ToolError(f"argument '{key}' must be {props[key]['type']}")
        if not isinstance(value, expected):
            raise ToolError(f"argument '{key}' must be {props[key].get('type')}")


class ToolRegistry:
    def __init__(self, tools: list[Tool]) -> None:
        self._tools = {t.name: t for t in tools}

    def specs(self) -> list[dict]:
        return [{"name": t.name, "description": t.description, "input_schema": t.input_schema}
                for t in self._tools.values()]

    def execute(self, name: str, args: dict) -> str:
        tool = self._tools.get(name)
        if tool is None:
            raise ToolError(f"unknown tool '{name}'. Available: {sorted(self._tools)}")
        validate_args(tool.input_schema, args)
        return tool.fn(**args)
