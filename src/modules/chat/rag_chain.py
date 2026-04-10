from __future__ import annotations

import time
from dataclasses import dataclass
from uuid import UUID

from langchain_openai import ChatOpenAI
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.modules.chat.models import Message
from src.modules.chat.prompt_templates import format_context, get_rag_prompt
from src.modules.knowledge.retriever import RetrieverService


@dataclass(slots=True)
class RAGResponse:
    content: str
    sources: list[dict]
    confidence: float
    escalated: bool
    response_time_ms: int


class RAGChain:
    def __init__(
        self,
        db: AsyncSession,
        retriever: RetrieverService,
        static_settings: Settings,
        model: str,
        temperature: float,
        max_tokens: int,
        escalation_threshold: float,
        clinic_name: str,
        owned_redis: Redis | None = None,
    ) -> None:
        self.db = db
        self.retriever = retriever
        self.static_settings = static_settings
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.escalation_threshold = escalation_threshold
        self.clinic_name = clinic_name
        self._owned_redis = owned_redis
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            api_key=static_settings.openai_api_key,
        )

    @classmethod
    async def from_settings(cls, db: AsyncSession, static_settings: Settings) -> 'RAGChain':
        """Cria RAGChain com configuracoes dinamicas do banco."""
        from src.modules.settings.service import SettingsService

        svc = SettingsService(db)
        ai_config = await svc.get_category_values('ai')
        bot_config = await svc.get_category_values('bot')
        redis = Redis.from_url(static_settings.redis_url, decode_responses=True)
        retriever = RetrieverService(db, redis, static_settings)

        return cls(
            db=db,
            retriever=retriever,
            static_settings=static_settings,
            model=str(ai_config.get('model', 'gpt-4o')),
            temperature=float(ai_config.get('temperature', 0.3)),
            max_tokens=int(ai_config.get('max_tokens', 500)),
            escalation_threshold=float(ai_config.get('escalation_threshold', static_settings.escalation_threshold)),
            clinic_name=str(bot_config.get('clinic_name', static_settings.clinic_name)),
            owned_redis=redis,
        )

    async def generate(self, question: str, conversation_id: UUID) -> RAGResponse:
        start = time.perf_counter()
        try:
            history_rows = (await self.db.execute(select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.desc()).limit(5))).scalars().all()
            history = '\n'.join(reversed([f'{m.role.value}: {m.content}' for m in history_rows]))
            chunks = await self.retriever.search(question)
            if not chunks:
                return RAGResponse(content='Vou encaminhar sua duvida para nossa equipe, que entrara em contato em breve.', sources=[], confidence=0.0, escalated=True, response_time_ms=int((time.perf_counter()-start)*1000))
            chain = get_rag_prompt(self.clinic_name) | self.llm
            ai = await chain.ainvoke({'context': format_context(chunks), 'history': history, 'question': question})
            content = str(ai.content)
            bonus = 0.0 if 'talvez' in content.lower() else 1.0
            confidence = min(1.0, max(0.0, (sum(c.score for c in chunks)/len(chunks))*0.7 + bonus*0.3))
            escalated = confidence < self.escalation_threshold
            if escalated:
                content = 'Vou encaminhar sua duvida para nossa equipe, que entrara em contato em breve.'
            return RAGResponse(content=content, sources=[{'chunk_id': c.chunk_id, 'score': c.score, 'document_title': c.document_title, 'metadata': c.metadata} for c in chunks], confidence=confidence, escalated=escalated, response_time_ms=int((time.perf_counter()-start)*1000))
        finally:
            if self._owned_redis is not None:
                await self._owned_redis.aclose()
