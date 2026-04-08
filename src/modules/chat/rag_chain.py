from __future__ import annotations

import time
from dataclasses import dataclass
from uuid import UUID

from langchain_openai import ChatOpenAI
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
    def __init__(self, db: AsyncSession, retriever: RetrieverService, settings: Settings) -> None:
        self.db = db
        self.retriever = retriever
        self.settings = settings
        self.llm = ChatOpenAI(model='gpt-4o', temperature=0.3, max_tokens=500, api_key=settings.openai_api_key)

    async def generate(self, question: str, conversation_id: UUID) -> RAGResponse:
        start = time.perf_counter()
        history_rows = (await self.db.execute(select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.desc()).limit(5))).scalars().all()
        history = '\n'.join(reversed([f'{m.role.value}: {m.content}' for m in history_rows]))
        chunks = await self.retriever.search(question)
        if not chunks:
            return RAGResponse(content='Vou encaminhar sua duvida para nossa equipe, que entrara em contato em breve.', sources=[], confidence=0.0, escalated=True, response_time_ms=int((time.perf_counter()-start)*1000))
        chain = get_rag_prompt(self.settings.clinic_name) | self.llm
        ai = await chain.ainvoke({'context': format_context(chunks), 'history': history, 'question': question})
        content = str(ai.content)
        bonus = 0.0 if 'talvez' in content.lower() else 1.0
        confidence = min(1.0, max(0.0, (sum(c.score for c in chunks)/len(chunks))*0.7 + bonus*0.3))
        escalated = confidence < self.settings.escalation_threshold
        if escalated:
            content = 'Vou encaminhar sua duvida para nossa equipe, que entrara em contato em breve.'
        return RAGResponse(content=content, sources=[{'chunk_id': c.chunk_id, 'score': c.score, 'document_title': c.document_title, 'metadata': c.metadata} for c in chunks], confidence=confidence, escalated=escalated, response_time_ms=int((time.perf_counter()-start)*1000))
