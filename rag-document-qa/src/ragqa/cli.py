"""Command line interface: ``python -m ragqa.cli "your question"``."""
from __future__ import annotations

import argparse

from .factory import build_pipeline


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Ask questions about your documents.")
    parser.add_argument("question")
    parser.add_argument("--docs", default=None, help="directory with .md/.txt files")
    parser.add_argument("--provider", choices=["extractive", "anthropic"], default=None)
    args = parser.parse_args(argv)

    result = build_pipeline(args.docs, args.provider).answer(args.question)
    print(result.text)
    for i, s in enumerate(result.sources, 1):
        print(f"  [{i}] {s.source} (score={s.score})")


if __name__ == "__main__":
    main()
