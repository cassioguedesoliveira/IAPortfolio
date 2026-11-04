"""CLI.

    evalkit run     --dataset datasets/qa.jsonl --model examples.models:good_model --out run.json
    evalkit compare --baseline baseline.json --new run.json --max-drop 0.02   # exit code 1 on regression
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

from .compare import compare_runs
from .dataset import load_dataset
from .report import to_markdown
from .runner import run_eval


def _load_callable(spec: str):
    module_name, _, attr = spec.partition(":")
    if not attr:
        raise SystemExit("--model must look like 'package.module:function'")
    return getattr(importlib.import_module(module_name), attr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="evalkit")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="evaluate a model on a dataset")
    run.add_argument("--dataset", required=True)
    run.add_argument("--model", required=True, help="module:function taking a str and returning a str")
    run.add_argument("--name", default=None)
    run.add_argument("--out", default="run.json")

    cmp_ = sub.add_parser("compare", help="fail if a run regressed against a baseline")
    cmp_.add_argument("--baseline", required=True)
    cmp_.add_argument("--new", required=True)
    cmp_.add_argument("--max-drop", type=float, default=0.02)

    args = parser.parse_args(argv)

    if args.cmd == "run":
        sys.path.insert(0, ".")
        result = run_eval(args.name or args.model, _load_callable(args.model), load_dataset(args.dataset))
        Path(args.out).write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
        print(to_markdown(result))
        return 0

    baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    new = json.loads(Path(args.new).read_text(encoding="utf-8"))
    comparison = compare_runs(baseline, new, max_drop=args.max_drop)
    print(comparison.to_markdown())
    return 0 if comparison.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
