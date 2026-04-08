from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from src.modules.chat.models import ConversationStatus, MessageRole


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    sources: list[dict]
    confidence: float
    escalated: bool
    conversation_id: str
    response_time_ms: int


class ConversationResponse(BaseModel):
    id: str
    status: ConversationStatus
    started_at: datetime
    last_message_at: datetime
    message_count: int
    resolved_without_human: bool


class ConversationPage(BaseModel):
    items: list[ConversationResponse]
    total: int
    page: int
    size: int


class MessageResponse(BaseModel):
    id: str
    role: MessageRole
    content: str
    sources_used: list | None
    confidence: float | None
    response_time_ms: int | None
    created_at: datetime
