"""Build a pipeline from environment variables (shared by CLI and API)."""
from __future__ import annotations

import os

from .chunking import load_directory
from .llm import AnthropicLLM, ExtractiveLLM
from .pipeline import RagPipeline
from .retriever import BM25Retriever


def build_pipeline(docs_dir: str | None = None, provider: str | None = None) -> RagPipeline:
    docs_dir = docs_dir or os.environ.get("DOCS_DIR", "data/docs")
    provider = provider or os.environ.get("LLM_PROVIDER", "extractive")
    retriever = BM25Retriever()
    retriever.index(load_directory(docs_dir))
    llm = AnthropicLLM() if provider == "anthropic" else ExtractiveLLM()
    return RagPipeline(retriever, llm)
