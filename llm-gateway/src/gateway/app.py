"""HTTP layer. Run: ``uvicorn gateway.app:app`` (requires fastapi + uvicorn)."""
from __future__ import annotations

import math

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .config import build_gateway
from .errors import AllProvidersFailed, RateLimitExceeded

app = FastAPI(title="LLM Gateway", version="1.0.0")
gw = build_gateway()


class CompleteRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=20000)
    max_tokens: int = Field(default=256, ge=1, le=4096)


class CompleteResponse(BaseModel):
    text: str
    provider: str
    model: str
    cached: bool
    cost_usd: float
    attempts: int


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics")
def metrics() -> dict:
    return gw.metrics.snapshot() | {"breakers": {n: b.state for n, b in gw.breakers.items()}}


@app.post("/v1/complete", response_model=CompleteResponse)
def complete(req: CompleteRequest, x_api_key: str = Header(...)) -> CompleteResponse:
    try:
        r = gw.complete(x_api_key, req.prompt, req.max_tokens)
    except RateLimitExceeded as exc:
        raise HTTPException(429, "rate limit exceeded", headers={"Retry-After": str(math.ceil(exc.retry_after))}) from exc
    except AllProvidersFailed as exc:
        raise HTTPException(502, {"error": "all providers failed", "providers": exc.failures}) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return CompleteResponse(**r.__dict__)
