"""Deterministic metrics. Every metric returns a score in [0, 1]."""
from __future__ import annotations

import json
import re
import string
from collections import Counter
from typing import Callable

Metric = Callable[[str, str, dict], float]


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = "".join(c for c in text if c not in string.punctuation)
    return re.sub(r"\s+", " ", text)


def exact_match(output: str, expected: str, params: dict) -> float:
    return float(_normalize(output) == _normalize(expected))


def contains(output: str, expected: str, params: dict) -> float:
    return float(_normalize(expected) in _normalize(output))


def token_f1(output: str, expected: str, params: dict) -> float:
    pred, gold = _normalize(output).split(), _normalize(expected).split()
    if not pred or not gold:
        return float(pred == gold)
    common = sum((Counter(pred) & Counter(gold)).values())
    if common == 0:
        return 0.0
    precision, recall = common / len(pred), common / len(gold)
    return 2 * precision * recall / (precision + recall)


def regex_match(output: str, expected: str, params: dict) -> float:
    """``expected`` is treated as a regular expression."""
    return float(re.search(expected, output, flags=re.I | re.S) is not None)


def json_fields(output: str, expected: str, params: dict) -> float:
    """Fraction of expected JSON fields reproduced exactly (structured extraction).

    Tolerates markdown code fences around the model output. Invalid JSON scores 0.
    """
    cleaned = re.sub(r"^```(?:json)?|```$", "", output.strip(), flags=re.M).strip()
    try:
        got, want = json.loads(cleaned), json.loads(expected)
    except json.JSONDecodeError:
        return 0.0
    if not isinstance(got, dict) or not isinstance(want, dict) or not want:
        return 0.0
    return sum(1 for k, v in want.items() if got.get(k) == v) / len(want)


REGISTRY: dict[str, Metric] = {
    "exact_match": exact_match,
    "contains": contains,
    "token_f1": token_f1,
    "regex_match": regex_match,
    "json_fields": json_fields,
}


def get_metric(name: str) -> Metric:
    try:
        return REGISTRY[name]
    except KeyError:
        raise KeyError(f"Unknown metric {name!r}. Available: {sorted(REGISTRY)}") from None
