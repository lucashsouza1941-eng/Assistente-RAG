from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class ConversationStatus(enum.StrEnum):
    ACTIVE = 'ACTIVE'
    CLOSED = 'CLOSED'
    ESCALATED = 'ESCALATED'


class MessageRole(enum.StrEnum):
    USER = 'USER'
    ASSISTANT = 'ASSISTANT'
    SYSTEM = 'SYSTEM'


class Conversation(Base):
    __tablename__ = 'conversations'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    whatsapp_number_hash: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[ConversationStatus] = mapped_column(Enum(ConversationStatus, name='conversation_status'), default=ConversationStatus.ACTIVE)
    started_at: Mapped[datetime] = mapped_column(server_default=func.now())
    last_message_at: Mapped[datetime] = mapped_column(server_default=func.now())
    message_count: Mapped[int] = mapped_column(default=0)
    resolved_without_human: Mapped[bool] = mapped_column(default=False)

    messages: Mapped[list[Message]] = relationship(back_populates='conversation', cascade='all, delete-orphan')


class Message(Base):
    __tablename__ = 'messages'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey('conversations.id', ondelete='CASCADE'))
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole, name='message_role'))
    content: Mapped[str] = mapped_column(Text)
    sources_used: Mapped[list[object] | None] = mapped_column(JSONB, nullable=True)
    confidence: Mapped[float | None] = mapped_column(nullable=True)
    response_time_ms: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    conversation: Mapped[Conversation] = relationship(back_populates='messages')
