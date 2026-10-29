"""FastAPI service exposing each sub-task and the end-to-end triage workflow.

Run:  uvicorn app.api:app --port 8000      Docs: http://localhost:8000/docs
"""
import time

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app import llm, tasks

app = FastAPI(title="Market Ops Ticket Copilot API", version="1.0",
              description="NLP sub-tasks for electricity-market operations tickets")


class TextIn(BaseModel):
    text: str = Field(..., min_length=5, examples=["Invoice INV-123456 for May does not match the line items."])


class ChatTurn(BaseModel):
    role: str
    content: str


class QuestionIn(BaseModel):
    question: str = Field(..., min_length=3)
    history: list[ChatTurn] = []
    k: int = Field(4, ge=1, le=10)


def timed(fn, *args, **kwargs):
    start = time.perf_counter()
    try:
        result = fn(*args, **kwargs)
    except FileNotFoundError as e:
        raise HTTPException(503, f"Model or index not built yet: {e}")
    result["latency_ms"] = round((time.perf_counter() - start) * 1000)
    return result


@app.get("/health")
def health():
    return {"status": "ok", "llm_backend": llm.backend(), "llm_model": llm.model_name()}


@app.post("/classify")
def classify(body: TextIn):
    return timed(tasks.classify, body.text)


@app.post("/summarize")
def summarize(body: TextIn):
    return timed(tasks.summarize, body.text)


@app.post("/extract")
def extract(body: TextIn):
    return timed(tasks.extract, body.text)


@app.post("/rag/ask")
def ask(body: QuestionIn):
    history = [t.model_dump() for t in body.history]
    return timed(tasks.ask, body.question, history, body.k)


@app.post("/triage")
def triage(body: TextIn):
    return timed(tasks.triage, body.text)
