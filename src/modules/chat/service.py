from __future__ import annotations

from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.modules.chat.rag_chain import RAGChain, RAGResponse
from src.modules.knowledge.retriever import RetrieverService


class ConversationService:
    def __init__(self, db: AsyncSession, redis: Redis, settings: Settings) -> None:
        self.db = db
        self.redis = redis
        self.settings = settings

    async def answer(self, question: str, conversation_id: UUID) -> RAGResponse:
        retriever = RetrieverService(self.db, self.redis, self.settings)
        rag_chain = RAGChain(self.db, retriever, self.settings)
        return await rag_chain.generate(question=question, conversation_id=conversation_id)
