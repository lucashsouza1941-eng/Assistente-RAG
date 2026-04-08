from __future__ import annotations

import enum
from datetime import datetime

from pydantic import BaseModel

from src.modules.chat.models import ConversationStatus, MessageRole
from src.schemas.pagination import Page


class PeriodFilter(str, enum.Enum):
    TODAY = 'today'
    DAYS_7 = '7d'
    DAYS_30 = '30d'


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


class ConversationPage(Page[ConversationResponse]):
    pass


class MessageResponse(BaseModel):
    id: str
    role: MessageRole
    content: str
    created_at: datetime
