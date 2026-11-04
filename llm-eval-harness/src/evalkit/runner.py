"""Run a model function over a dataset and collect scores, latency and errors."""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from statistics import mean
from typing import Callable

from .dataset import Case
from .metrics import Metric, get_metric

ModelFn = Callable[[str], str]


@dataclass
class CaseResult:
    id: str
    tags: list[str]
    output: str
    scores: dict[str, float]
    latency_ms: float
    error: str | None = None

    @property
    def score(self) -> float:
        return mean(self.scores.values()) if self.scores else 0.0


@dataclass
class RunResult:
    name: str
    cases: list[CaseResult] = field(default_factory=list)

    @property
    def mean_score(self) -> float:
        return mean(c.score for c in self.cases) if self.cases else 0.0

    @property
    def error_rate(self) -> float:
        return sum(c.error is not None for c in self.cases) / len(self.cases) if self.cases else 0.0

    def by_tag(self) -> dict[str, float]:
        buckets: dict[str, list[float]] = {}
        for c in self.cases:
            for tag in c.tags:
                buckets.setdefault(tag, []).append(c.score)
        return {tag: mean(v) for tag, v in sorted(buckets.items())}

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "mean_score": self.mean_score,
            "error_rate": self.error_rate,
            "by_tag": self.by_tag(),
            "cases": [asdict(c) | {"score": c.score} for c in self.cases],
        }


def run_eval(
    name: str,
    model: ModelFn,
    cases: list[Case],
    extra_metrics: dict[str, Metric] | None = None,
) -> RunResult:
    """Evaluate ``model`` on ``cases``. A crashing model call counts as score 0, not a crash of the run."""
    extra = extra_metrics or {}
    result = RunResult(name=name)
    for case in cases:
        start = time.perf_counter()
        output, error = "", None
        try:
            output = model(case.input)
        except Exception as exc:  # noqa: BLE001 - we want to record any failure
            error = f"{type(exc).__name__}: {exc}"
        latency = (time.perf_counter() - start) * 1000

        scores: dict[str, float] = {}
        for metric_name in case.metrics:
            metric = extra.get(metric_name) or get_metric(metric_name)
            scores[metric_name] = 0.0 if error else metric(output, case.expected, {"question": case.input, **case.params})
        result.cases.append(CaseResult(case.id, list(case.tags), output, scores, latency, error))
    return result
