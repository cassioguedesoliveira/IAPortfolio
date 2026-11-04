# evalkit: LLM Evaluation Harness with CI Regression Gate

> Treat prompts and models like code: test them. `evalkit` scores an LLM application against a golden dataset and **fails your pull request when quality drops**.

Changing a prompt, swapping a model or tweaking retrieval can silently break behaviour that used to work. Most teams discover it from users. `evalkit` is a small, dependency-free harness that makes those regressions visible in CI.

## Features

- **Golden datasets in JSONL**: one case per line, with tags and per-case metrics. Duplicate ids and malformed lines are rejected with line numbers.
- **Deterministic metrics**: `exact_match`, `contains`, `token_f1`, `regex_match`, `json_fields` (structured extraction, tolerates markdown fences).
- **LLM-as-judge** for open-ended answers, with a rubric prompt and fail-closed parsing: an unparseable judge reply scores 0 instead of inflating results.
- **Robust runner**: a model call that raises is recorded as an error with score 0; the run itself never crashes. Latency is tracked per case.
- **Slice analysis**: scores aggregated per tag, so you see *what* regressed (e.g. only `safety`), not just that the average moved.
- **Regression gate**: `evalkit compare` exits with code 1 if the mean score drops more than a threshold and lists regressed cases.
- **Zero runtime dependencies**, 11 unit tests, GitHub Actions workflow included.

## Quick start

```bash
pip install -e .

# 1. Evaluate a model (any `module:function` taking a str and returning a str)
evalkit run --dataset datasets/qa.jsonl --model examples.models:good_model --out baselines/main.json

# 2. Evaluate a changed version and compare
evalkit run --dataset datasets/qa.jsonl --model examples.models:worse_model --out run.json
evalkit compare --baseline baselines/main.json --new run.json --max-drop 0.02
```

Output of the comparison (a deliberately degraded model):

```
## Eval comparison: FAIL
- baseline: 1.000
- new: 0.625 (delta -0.375, allowed drop 0.020)

| tag | delta |
|---|---|
| extraction | -0.500 |
| factual | +0.000 |
| math | -0.500 |
| safety | -1.000 |
| summarization | +0.000 |

Regressed cases: extract-2, math-1, safety-1
```

### Plug in a real model

```python
# my_app.py
import anthropic
client = anthropic.Anthropic()

def my_model(prompt: str) -> str:
    msg = client.messages.create(model="claude-sonnet-5-5", max_tokens=300,
                                 messages=[{"role": "user", "content": prompt}])
    return msg.content[0].text
```

```bash
evalkit run --dataset datasets/qa.jsonl --model my_app:my_model
```

### LLM-as-judge

```python
from evalkit import run_eval, load_dataset
from evalkit.judge import make_judge_metric

judge = make_judge_metric(lambda prompt: my_model(prompt))   # ideally a stronger model than the one under test
result = run_eval("v2", my_model, load_dataset("datasets/open_ended.jsonl"), extra_metrics={"llm_judge": judge})
```

Use `"metrics": ["llm_judge"]` in the dataset cases that need it.

## Dataset format

```json
{"id": "extract-1", "input": "Extract JSON ...", "expected": "{\"name\": \"Ana\"}", "tags": ["extraction"], "metrics": ["json_fields"]}
```

## CI integration

`.github/workflows/ci.yml` contains an `eval-gate` job: it runs the evaluation on every PR and compares with the committed baseline (`baselines/main.json`). Update the baseline deliberately when you accept a behaviour change, so the diff is reviewed like any other change.

## Design notes

- **Why not just use accuracy?** A single number hides failures. Tags and per-case diffs tell you which capability moved.
- **Fail closed.** Errors, invalid JSON and unparseable judge replies all score 0. A silent pass is worse than a loud failure.
- **Judge calibration.** LLM judges are biased (verbosity, self-preference). Use a different/stronger model than the one being judged, keep rubric scores coarse, and spot-check against human labels.
- **Noise.** With small datasets a 1-case change can move the mean a lot. Keep `--max-drop` realistic and grow the dataset from production failures.

## Limitations and next steps

- No parallel execution or caching of model calls yet (a thread pool plus on-disk cache keyed by prompt hash is the natural next step).
- No confidence intervals; add bootstrap resampling to separate real regressions from noise.
- Add embedding-based semantic similarity and RAG-specific metrics (faithfulness, context precision).
- Export results to a dashboard (HTML report) for trend tracking across runs.

## Layout

```
src/evalkit/   dataset, metrics, judge, runner, compare, report, cli
datasets/      golden data       examples/   offline stub models
tests/         unit tests        baselines/  committed baseline for the CI gate
```
