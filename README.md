# AI Engineering Portfolio

Five projects covering applied LLM engineering (four in Python) and a full-stack Java + Angular application. Each one has its own README, tests that run offline (no API key needed), CI, and a clear list of limitations and next steps.

| Project | What it shows | Stack |
|---|---|---|
| [`rag-document-qa`](rag-document-qa) | Retrieval-Augmented Generation with citations and a refusal guardrail; measured retrieval quality | Python, BM25, FastAPI, Docker, Claude API |
| [`llm-eval-harness`](llm-eval-harness) | Evaluating LLM apps: golden datasets, metrics, LLM-as-judge, regression gate in CI | Python, GitHub Actions |
| [`ticket-triage-agent`](ticket-triage-agent) | Tool-using agent with validation, policy guardrails, PII redaction and audit trail | Python, Claude tool use |
| [`llm-gateway`](llm-gateway) | Reliability layer: cache, rate limit, retries, circuit breaker, fallback, cost tracking | Python, FastAPI, Docker |
| [`meeting-actions-tracker`](meeting-actions-tracker) | Full-stack app: notes to tracked action items, LLM with rule-based fallback | Java 21, Spring Boot, JPA, PostgreSQL, Angular 19, Docker Compose |

The projects are designed to work together: use `llm-eval-harness` to score the answers from `rag-document-qa` or the decisions of `ticket-triage-agent`, and put `llm-gateway` in front of either one.

## Running everything

```bash
for p in rag-document-qa llm-eval-harness ticket-triage-agent llm-gateway; do
  (cd $p && PYTHONPATH=src:. python -m unittest discover -s tests)
done
```

The Java/Angular project has its own instructions (Maven + npm) and a section stating exactly what has and has not been verified.
