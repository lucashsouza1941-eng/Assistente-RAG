from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID, uuid4

from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.modules.chat.models import Conversation, Message, MessageRole
from src.modules.chat.rag_chain import RAGChain
from src.modules.chat.schemas import PeriodFilter
from src.modules.knowledge.retriever import RetrieverService


class ConversationService:
    def __init__(self, db: AsyncSession, redis: Redis, settings: Settings) -> None:
        self.db = db
        self.redis = redis
        self.settings = settings

    async def send(self, message: str, conversation_id: UUID | None):
        conversation = await self._get_or_create(conversation_id)
        self.db.add(Message(conversation_id=conversation.id, role=MessageRole.USER, content=message))
        retriever = RetrieverService(self.db, self.redis, self.settings)
        response = await RAGChain(self.db, retriever, self.settings).generate(message, conversation.id)
        self.db.add(Message(conversation_id=conversation.id, role=MessageRole.ASSISTANT, content=response.content, sources_used=response.sources, confidence=response.confidence, response_time_ms=response.response_time_ms))
        await self.db.commit()
        return conversation, response

    async def list_conversations(self, page: int, size: int, period: PeriodFilter | None):
        stmt = select(Conversation).order_by(Conversation.started_at.desc())
        count_stmt = select(func.count(Conversation.id))
        if period is not None:
            now = datetime.utcnow()
            days = 1 if period == PeriodFilter.TODAY else (7 if period == PeriodFilter.DAYS_7 else 30)
            since = now - timedelta(days=days)
            stmt = stmt.where(Conversation.started_at >= since)
            count_stmt = count_stmt.where(Conversation.started_at >= since)
        items = (await self.db.execute(stmt.offset((page - 1) * size).limit(size))).scalars().all()
        total = int(await self.db.scalar(count_stmt) or 0)
        return list(items), total

    async def list_messages(self, conversation_id: UUID) -> list[Message]:
        if await self.db.get(Conversation, conversation_id) is None:
            raise ValueError('Conversation not found')
        rows = (await self.db.execute(select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()))).scalars().all()
        return list(rows)

    async def _get_or_create(self, conversation_id: UUID | None) -> Conversation:
        if conversation_id is not None:
            c = await self.db.scalar(select(Conversation).where(Conversation.id == conversation_id))
            if c is not None:
                return c
        c = Conversation(id=uuid4(), whatsapp_number_hash=f'web-{uuid4().hex}')
        self.db.add(c)
        await self.db.flush()
        return c
