from __future__ import annotations

import time
from dataclasses import dataclass
from uuid import UUID

from langchain_openai import ChatOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.modules.chat.models import Conversation, Message
from src.modules.chat.prompt_templates import format_context, get_rag_prompt
from src.modules.knowledge.retriever import RetrievedChunk, RetrieverService

ESCALATION_MESSAGE = 'Vou encaminhar sua duvida para nossa equipe, que entrara em contato em breve.'

UNCERTAINTY_MARKERS = (
    'nao tenho certeza',
    'talvez',
    'nao sei',
    'nao esta claro',
    'nao encontrei',
)


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
        settings: Settings,
    ) -> None:
        self.db = db
        self.retriever = retriever
        self.settings = settings
        self.llm = ChatOpenAI(
            model='gpt-4o',
            temperature=0.3,
            max_tokens=500,
            api_key=settings.openai_api_key,
        )

    async def generate(self, question: str, conversation_id: UUID) -> RAGResponse:
        started = time.perf_counter()

        history = await self._get_history(conversation_id)
        retrieved = await self.retriever.search(question)

        if not retrieved:
            response_time_ms = int((time.perf_counter() - started) * 1000)
            return RAGResponse(
                content=ESCALATION_MESSAGE,
                sources=[],
                confidence=0.0,
                escalated=True,
                response_time_ms=response_time_ms,
            )

        prompt = get_rag_prompt(self.settings.clinic_name)
        chain = prompt | self.llm

        context_text = format_context(retrieved)
        ai_message = await chain.ainvoke({'context': context_text, 'history': history, 'question': question})
        answer_text = str(ai_message.content)

        confidence = self._calculate_confidence(retrieved, answer_text)
        escalated = confidence < self.settings.escalation_threshold
        final_content = ESCALATION_MESSAGE if escalated else answer_text

        response_time_ms = int((time.perf_counter() - started) * 1000)
        return RAGResponse(
            content=final_content,
            sources=[
                {
                    'chunk_id': chunk.chunk_id,
                    'document_title': chunk.document_title,
                    'score': chunk.score,
                    'metadata': chunk.metadata,
                }
                for chunk in retrieved
            ],
            confidence=confidence,
            escalated=escalated,
            response_time_ms=response_time_ms,
        )

    async def _get_history(self, conversation_id: UUID) -> str:
        conversation = await self.db.scalar(select(Conversation).where(Conversation.id == conversation_id))
        if conversation is None:
            return ''

        messages_stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(5)
        )
        result = await self.db.execute(messages_stmt)
        messages = list(reversed(result.scalars().all()))

        return '\n'.join(f'{message.role.value}: {message.content}' for message in messages)

    def _calculate_confidence(self, chunks: list[RetrievedChunk], answer: str) -> float:
        avg_score = sum(chunk.score for chunk in chunks) / len(chunks)
        lowered = answer.lower()
        has_uncertainty = any(marker in lowered for marker in UNCERTAINTY_MARKERS)
        keyword_bonus = 0.0 if has_uncertainty else 1.0
        confidence = (avg_score * 0.7) + (keyword_bonus * 0.3)
        return max(0.0, min(1.0, confidence))
