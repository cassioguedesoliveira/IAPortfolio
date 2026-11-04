"""Retrieve -> guard -> generate -> cite."""
from __future__ import annotations

from dataclasses import dataclass, field

from .llm import LLM
from .retriever import BM25Retriever

NO_ANSWER = "I could not find this in the provided documents."
SYSTEM_PROMPT = (
    "You answer questions using ONLY the numbered context passages provided. "
    "Cite the passages you used like [1] or [2]. "
    f"If the context does not contain the answer, reply exactly: '{NO_ANSWER}' "
    "Never use outside knowledge."
)


@dataclass
class Source:
    id: str
    source: str
    score: float
    text: str


@dataclass
class Answer:
    text: str
    sources: list[Source] = field(default_factory=list)
    grounded: bool = True


class RagPipeline:
    def __init__(self, retriever: BM25Retriever, llm: LLM, top_k: int = 4, min_score: float = 0.5) -> None:
        self.retriever, self.llm = retriever, llm
        self.top_k, self.min_score = top_k, min_score

    def answer(self, question: str) -> Answer:
        question = question.strip()
        if not question:
            raise ValueError("question must not be empty")

        hits = [h for h in self.retriever.search(question, self.top_k) if h.score >= self.min_score]
        # Guardrail: with no relevant evidence we refuse instead of letting the model guess.
        if not hits:
            return Answer(text=NO_ANSWER, grounded=False)

        context = "\n\n".join(f"[{i}] ({h.chunk.source})\n{h.chunk.text}" for i, h in enumerate(hits, 1))
        prompt = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer with citations:"
        text = self.llm.generate(SYSTEM_PROMPT, prompt)
        sources = [Source(h.chunk.id, h.chunk.source, round(h.score, 3), h.chunk.text) for h in hits]
        return Answer(text=text, sources=sources, grounded=NO_ANSWER not in text)
