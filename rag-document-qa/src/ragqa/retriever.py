"""BM25 lexical retriever implemented from scratch (no heavy dependencies).

BM25 is a strong baseline and needs no embedding model. The retriever
interface is intentionally tiny so a vector-based retriever can be swapped in.
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass

from .chunking import Chunk

_STOPWORDS = frozenset(
    "a an and are as at be by for from how i in is it of on or that the this to was what when where which who "
    "with do does can my me you your "
    "o os as um uma de da do das dos e em para por com que qual quais como quando onde é são no na nos nas ao".split()
)


def tokenize(text: str) -> list[str]:
    """Lowercase, strip accents, split on non-word characters, drop stopwords."""
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    stop = {"".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)) for s in _STOPWORDS}
    return [_stem(t) for t in re.findall(r"\w+", text) if t not in stop]


def _stem(token: str) -> str:
    """Very light plural stemmer ("passwords" -> "password"). Swap for a real stemmer if needed."""
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float


class BM25Retriever:
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1, self.b = k1, b
        self._chunks: list[Chunk] = []
        self._tf: list[Counter[str]] = []
        self._df: Counter[str] = Counter()
        self._avg_len = 0.0

    def index(self, chunks: list[Chunk]) -> None:
        self._chunks = list(chunks)
        self._tf = [Counter(tokenize(c.text)) for c in self._chunks]
        self._df = Counter(term for tf in self._tf for term in tf)
        total = sum(sum(tf.values()) for tf in self._tf)
        self._avg_len = total / len(self._tf) if self._tf else 0.0

    def __len__(self) -> int:
        return len(self._chunks)

    def _idf(self, term: str) -> float:
        n, df = len(self._chunks), self._df.get(term, 0)
        return math.log(1 + (n - df + 0.5) / (df + 0.5))

    def search(self, query: str, top_k: int = 4) -> list[Hit]:
        terms = tokenize(query)
        hits: list[Hit] = []
        for chunk, tf in zip(self._chunks, self._tf):
            doc_len = sum(tf.values()) or 1
            score = 0.0
            for term in terms:
                f = tf.get(term, 0)
                if not f:
                    continue
                denom = f + self.k1 * (1 - self.b + self.b * doc_len / (self._avg_len or 1))
                score += self._idf(term) * f * (self.k1 + 1) / denom
            if score > 0:
                hits.append(Hit(chunk, score))
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:top_k]
