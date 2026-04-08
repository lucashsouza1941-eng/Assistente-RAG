from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID, uuid4

from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.modules.chat.models import Conversation, ConversationStatus, Message, MessageRole
from src.modules.chat.rag_chain import RAGChain, RAGResponse
from src.modules.knowledge.retriever import RetrieverService


class ConversationService:
    def __init__(self, db: AsyncSession, redis: Redis, settings: Settings) -> None:
        self.db = db
        self.redis = redis
        self.settings = settings

    async def send_message(self, message: str, conversation_id: UUID | None) -> tuple[Conversation, RAGResponse]:
        conversation = await self._get_or_create_conversation(conversation_id)
        self.db.add(Message(conversation_id=conversation.id, role=MessageRole.USER, content=message))
        conversation.message_count += 1

        retriever = RetrieverService(self.db, self.redis, self.settings)
        rag_chain = RAGChain(self.db, retriever, self.settings)
        response = await rag_chain.generate(question=message, conversation_id=conversation.id)

        self.db.add(Message(conversation_id=conversation.id, role=MessageRole.ASSISTANT, content=response.content, sources_used=response.sources, confidence=response.confidence, response_time_ms=response.response_time_ms))
        conversation.message_count += 1
        conversation.last_message_at = datetime.utcnow()
        if response.escalated:
            conversation.status = ConversationStatus.ESCALATED
        await self.db.commit()
        return conversation, response

    async def list_conversations(self, *, page: int, size: int, status: ConversationStatus | None, period: str | None) -> tuple[list[Conversation], int]:
        stmt = select(Conversation).order_by(Conversation.last_message_at.desc())
        count_stmt = select(func.count(Conversation.id))
        if status is not None:
            stmt = stmt.where(Conversation.status == status)
            count_stmt = count_stmt.where(Conversation.status == status)
        if period:
            now = datetime.utcnow()
            delta_map = {'today': timedelta(days=1), '7d': timedelta(days=7), '30d': timedelta(days=30)}
            if period in delta_map:
                since = now - delta_map[period]
                stmt = stmt.where(Conversation.started_at >= since)
                count_stmt = count_stmt.where(Conversation.started_at >= since)
        result = await self.db.execute(stmt.offset((page - 1) * size).limit(size))
        total = await self.db.scalar(count_stmt)
        return list(result.scalars().all()), int(total or 0)

    async def list_messages(self, conversation_id: UUID) -> list[Message]:
        result = await self.db.execute(select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()))
        return list(result.scalars().all())

    async def conversation_exists(self, conversation_id: UUID) -> bool:
        return (await self.db.scalar(select(Conversation.id).where(Conversation.id == conversation_id))) is not None

    async def _get_or_create_conversation(self, conversation_id: UUID | None) -> Conversation:
        if conversation_id is not None:
            existing = await self.db.scalar(select(Conversation).where(Conversation.id == conversation_id))
            if existing is not None:
                return existing
        conversation = Conversation(id=uuid4(), whatsapp_number_hash=f'web-{uuid4().hex}', status=ConversationStatus.ACTIVE)
        self.db.add(conversation)
        await self.db.flush()
        return conversation
