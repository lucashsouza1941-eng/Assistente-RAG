from __future__ import annotations

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    conversation_id: str


class ChatResponse(BaseModel):
    content: str
    sources: list[dict]
    confidence: float
    escalated: bool
    response_time_ms: int
