"""Demo: ``python -m triage.cli "I want a refund for ORD-1001"``."""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .agent import Agent
from .llm import AnthropicToolLLM, PolicyLLM
from .shop import Shop, build_tools
from .tools import ToolRegistry


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("ticket")
    parser.add_argument("--provider", choices=["offline", "anthropic"], default="offline")
    args = parser.parse_args(argv)

    shop = Shop()
    llm = AnthropicToolLLM() if args.provider == "anthropic" else PolicyLLM()
    result = Agent(llm, ToolRegistry(build_tools(shop))).run(args.ticket)
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
