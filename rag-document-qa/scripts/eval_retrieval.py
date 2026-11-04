"""Measure retrieval quality (hit rate@k and MRR) on a small golden set.

Run: PYTHONPATH=src python scripts/eval_retrieval.py
"""
from ragqa.chunking import load_directory
from ragqa.retriever import BM25Retriever

GOLDEN = [
    ("How many days can I work remotely?", "remote_work_policy.md"),
    ("What is the daily meal allowance when travelling?", "expense_policy.md"),
    ("How long do I have to submit receipts?", "expense_policy.md"),
    ("How long should my password be?", "security_policy.md"),
    ("Who do I tell if I lose my laptop?", "security_policy.md"),
    ("Is there a stipend for a home office?", "remote_work_policy.md"),
]


def main(k: int = 3) -> None:
    retriever = BM25Retriever()
    retriever.index(load_directory("data/docs"))
    hits_at_k, rr = 0, 0.0
    for question, expected in GOLDEN:
        sources = [h.chunk.source for h in retriever.search(question, k)]
        if expected in sources:
            hits_at_k += 1
            rr += 1 / (sources.index(expected) + 1)
    n = len(GOLDEN)
    print(f"hit_rate@{k}: {hits_at_k / n:.2f}   MRR: {rr / n:.2f}   (n={n})")


if __name__ == "__main__":
    main()
