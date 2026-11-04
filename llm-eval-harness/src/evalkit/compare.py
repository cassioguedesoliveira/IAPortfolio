"""Regression detection between a baseline run and a new run."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Comparison:
    baseline_score: float
    new_score: float
    delta: float
    regressed_cases: list[str]
    improved_cases: list[str]
    tag_deltas: dict[str, float]
    passed: bool
    max_drop: float

    def to_markdown(self) -> str:
        verdict = "PASS" if self.passed else "FAIL"
        lines = [
            f"## Eval comparison: {verdict}",
            f"- baseline: {self.baseline_score:.3f}",
            f"- new: {self.new_score:.3f} (delta {self.delta:+.3f}, allowed drop {self.max_drop:.3f})",
        ]
        if self.tag_deltas:
            lines += ["", "| tag | delta |", "|---|---|"]
            lines += [f"| {t} | {d:+.3f} |" for t, d in self.tag_deltas.items()]
        if self.regressed_cases:
            lines += ["", f"Regressed cases: {', '.join(self.regressed_cases)}"]
        if self.improved_cases:
            lines += ["", f"Improved cases: {', '.join(self.improved_cases)}"]
        return "\n".join(lines)


def compare_runs(baseline: dict, new: dict, max_drop: float = 0.02, case_tolerance: float = 0.05) -> Comparison:
    """Compare two ``RunResult.to_dict()`` payloads.

    The run fails if the mean score drops by more than ``max_drop``. Individual
    cases are flagged when they move by more than ``case_tolerance``.
    """
    base_cases = {c["id"]: c["score"] for c in baseline["cases"]}
    new_cases = {c["id"]: c["score"] for c in new["cases"]}
    shared = base_cases.keys() & new_cases.keys()

    regressed = sorted(i for i in shared if new_cases[i] < base_cases[i] - case_tolerance)
    improved = sorted(i for i in shared if new_cases[i] > base_cases[i] + case_tolerance)
    base_tags, new_tags = baseline.get("by_tag", {}), new.get("by_tag", {})
    tag_deltas = {t: new_tags[t] - base_tags[t] for t in sorted(base_tags.keys() & new_tags.keys())}

    delta = new["mean_score"] - baseline["mean_score"]
    return Comparison(
        baseline_score=baseline["mean_score"],
        new_score=new["mean_score"],
        delta=delta,
        regressed_cases=regressed,
        improved_cases=improved,
        tag_deltas=tag_deltas,
        passed=delta >= -max_drop,
        max_drop=max_drop,
    )
