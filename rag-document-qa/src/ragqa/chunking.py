"""Split documents into overlapping word-based chunks and load them from disk."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Chunk:
    id: str
    source: str
    text: str


def chunk_text(text: str, source: str, max_words: int = 120, overlap: int = 20) -> list[Chunk]:
    """Split ``text`` into chunks of at most ``max_words`` words.

    Consecutive chunks share ``overlap`` words so that a fact straddling a
    boundary is still retrievable.
    """
    if max_words <= 0:
        raise ValueError("max_words must be positive")
    if not 0 <= overlap < max_words:
        raise ValueError("overlap must be >= 0 and < max_words")

    words = text.split()
    if not words:
        return []

    step = max_words - overlap
    chunks: list[Chunk] = []
    for n, start in enumerate(range(0, len(words), step)):
        window = words[start : start + max_words]
        chunks.append(Chunk(id=f"{source}#{n}", source=source, text=" ".join(window)))
        if start + max_words >= len(words):
            break
    return chunks


def load_directory(path: str | Path, **chunk_kwargs) -> list[Chunk]:
    """Load every ``.md`` / ``.txt`` file under ``path`` and chunk it."""
    root = Path(path)
    if not root.is_dir():
        raise FileNotFoundError(f"Documents directory not found: {root}")
    chunks: list[Chunk] = []
    for file in sorted(root.rglob("*")):
        if file.suffix.lower() in {".md", ".txt"} and file.is_file():
            chunks.extend(chunk_text(file.read_text(encoding="utf-8"), file.name, **chunk_kwargs))
    return chunks
