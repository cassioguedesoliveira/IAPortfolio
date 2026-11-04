"""Golden dataset format (JSONL), one case per line.

    {"id": "q1", "input": "...", "expected": "...", "tags": ["math"], "metrics": ["exact_match"]}
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Case:
    id: str
    input: str
    expected: str
    tags: tuple[str, ...] = ()
    metrics: tuple[str, ...] = ("exact_match",)
    params: dict = field(default_factory=dict)


def load_dataset(path: str | Path) -> list[Case]:
    cases: list[Case] = []
    seen: set[str] = set()
    for lineno, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
            case = Case(
                id=str(raw["id"]),
                input=raw["input"],
                expected=raw["expected"],
                tags=tuple(raw.get("tags", ())),
                metrics=tuple(raw.get("metrics", ("exact_match",))),
                params=raw.get("params", {}),
            )
        except (json.JSONDecodeError, KeyError) as exc:
            raise ValueError(f"{path}:{lineno}: invalid case ({exc!r})") from exc
        if case.id in seen:
            raise ValueError(f"{path}:{lineno}: duplicate id {case.id!r}")
        seen.add(case.id)
        cases.append(case)
    return cases
