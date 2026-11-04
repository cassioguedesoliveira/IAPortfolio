"""evalkit: a lightweight evaluation harness for LLM applications."""
from .compare import compare_runs
from .dataset import Case, load_dataset
from .runner import RunResult, run_eval

__all__ = ["Case", "load_dataset", "run_eval", "RunResult", "compare_runs"]
