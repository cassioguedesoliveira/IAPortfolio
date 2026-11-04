"""Human-readable Markdown report for a run."""
from __future__ import annotations

from .runner import RunResult


def to_markdown(result: RunResult, worst: int = 5) -> str:
    lines = [
        f"# Eval report: {result.name}",
        "",
        f"- cases: {len(result.cases)}",
        f"- mean score: **{result.mean_score:.3f}**",
        f"- error rate: {result.error_rate:.1%}",
    ]
    latencies = sorted(c.latency_ms for c in result.cases)
    if latencies:
        p95 = latencies[min(len(latencies) - 1, int(0.95 * len(latencies)))]
        lines.append(f"- latency p50 / p95: {latencies[len(latencies) // 2]:.1f} ms / {p95:.1f} ms")
    if result.by_tag():
        lines += ["", "| tag | mean score |", "|---|---|"]
        lines += [f"| {t} | {s:.3f} |" for t, s in result.by_tag().items()]
    failing = sorted((c for c in result.cases if c.score < 1.0), key=lambda c: c.score)[:worst]
    if failing:
        lines += ["", f"## Lowest-scoring cases (top {len(failing)})"]
        for c in failing:
            detail = c.error or c.output.replace("\n", " ")[:120]
            lines.append(f"- `{c.id}` score={c.score:.2f}: {detail}")
    return "\n".join(lines)
