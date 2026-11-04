"""HTTP API. Run: ``uvicorn ragqa.api:app --reload`` (requires fastapi + uvicorn)."""
from __future__ import annotations

from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .factory import build_pipeline

app = FastAPI(title="RAG Document Q&A", version="1.0.0")
_pipeline = build_pipeline()


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class SourceOut(BaseModel):
    id: str
    source: str
    score: float
    text: str


class AskResponse(BaseModel):
    answer: str
    grounded: bool
    sources: list[SourceOut]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    try:
        result = _pipeline.answer(req.question)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return AskResponse(
        answer=result.text,
        grounded=result.grounded,
        sources=[SourceOut(**asdict(s)) for s in result.sources],
    )
