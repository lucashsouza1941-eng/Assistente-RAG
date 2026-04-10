from __future__ import annotations

import hashlib
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.core.logging import get_logger, sanitize_message
from src.modules.chat.models import Conversation, ConversationStatus, Message, MessageRole
from src.modules.chat.rag_chain import RAGChain
from src.modules.knowledge.retriever import RetrieverService
from src.modules.whatsapp.client import MetaAPIClient
from src.modules.whatsapp.schemas import WebhookMessage

log = get_logger(module='whatsapp.service')


class WhatsAppService:
    def __init__(self, db: AsyncSession, redis: Redis, settings: Settings, meta_client: MetaAPIClient) -> None:
        self.db = db
        self.redis = redis
        self.settings = settings
        self.meta_client = meta_client

    async def handle_message(self, message: WebhookMessage) -> None:
        conversation_id: UUID | None = None
        try:
            number_hash = hashlib.sha256(f'{message.from_}{self.settings.hash_salt}'.encode()).hexdigest()
            if not await self._allow(number_hash):
                return
            conv = await self._conversation(number_hash)
            conversation_id = conv.id
            text = message.text.body if message.text else ''
            self.db.add(Message(conversation_id=conv.id, role=MessageRole.USER, content=text))
            retriever = RetrieverService(self.db, self.redis, self.settings)
            rag = RAGChain(self.db, retriever, self.settings)
            response = await rag.generate(text, conv.id)
            self.db.add(Message(conversation_id=conv.id, role=MessageRole.ASSISTANT, content=response.content, sources_used=response.sources, confidence=response.confidence, response_time_ms=response.response_time_ms))
            if response.escalated:
                conv.status = ConversationStatus.ESCALATED
            await self.db.commit()
            await self.meta_client.send_text_message(message.from_, response.content)
            await self.meta_client.mark_as_read(message.id)
            log.info('whatsapp.handled', metadata={'number_hash': number_hash, 'message_preview': sanitize_message(text)})
        except Exception as exc:
            log.error(
                'whatsapp_message_handling_failed',
                error_type=type(exc).__name__,
                error_message=str(exc)[:200],
                conversation_id=str(conversation_id) if conversation_id else None,
            )
            await self.db.rollback()
            raise

    async def _allow(self, number_hash: str) -> bool:
        key = f'rate:{number_hash}'
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, 60)
        return count <= 20

    async def _conversation(self, number_hash: str) -> Conversation:
        conv = await self.db.scalar(select(Conversation).where(Conversation.whatsapp_number_hash == number_hash, Conversation.status == ConversationStatus.ACTIVE))
        if conv:
            return conv
        conv = Conversation(whatsapp_number_hash=number_hash)
        self.db.add(conv)
        await self.db.flush()
        return conv
