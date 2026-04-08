from __future__ import annotations

import hashlib

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.core.logging import get_logger
from src.modules.chat.models import Conversation, ConversationStatus, Message, MessageRole
from src.modules.chat.rag_chain import RAGChain
from src.modules.knowledge.retriever import RetrieverService
from src.modules.whatsapp.client import MetaAPIClient
from src.modules.whatsapp.schemas import WebhookMessage

logger = get_logger(__name__)


class WhatsAppService:
    def __init__(self, db: AsyncSession, redis: Redis, settings: Settings) -> None:
        self.db = db
        self.redis = redis
        self.settings = settings
        self.client = MetaAPIClient(settings)

    async def handle_message(self, message: WebhookMessage) -> None:
        try:
            phone_hash = self._hash_number(message.from_)

            if not await self._allow_message(phone_hash):
                logger.warning('whatsapp.rate_limited', number_hash=phone_hash)
                return

            conversation = await self._get_or_create_conversation(phone_hash)

            user_text = message.text.body if message.text else ''
            user_msg = Message(
                conversation_id=conversation.id,
                role=MessageRole.USER,
                content=user_text,
            )
            self.db.add(user_msg)
            conversation.message_count += 1
            await self.db.flush()

            retriever = RetrieverService(self.db, self.redis, self.settings)
            rag = RAGChain(self.db, retriever, self.settings)
            response = await rag.generate(user_text, conversation.id)

            assistant_msg = Message(
                conversation_id=conversation.id,
                role=MessageRole.ASSISTANT,
                content=response.content,
                sources_used=response.sources,
                confidence=response.confidence,
                response_time_ms=response.response_time_ms,
            )
            self.db.add(assistant_msg)
            conversation.message_count += 1

            if response.escalated:
                conversation.status = ConversationStatus.ESCALATED

            await self.db.commit()

            await self.client.send_text_message(message.from_, response.content)
            await self.client.mark_as_read(message.id)
        except Exception as exc:
            await self.db.rollback()
            logger.exception('whatsapp.handle_message_failed', error=str(exc))

    async def _allow_message(self, phone_hash: str) -> bool:
        key = f'whatsapp:rate:{phone_hash}'
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, 60)
        return count <= 20

    async def _get_or_create_conversation(self, phone_hash: str) -> Conversation:
        conversation = await self.db.scalar(
            select(Conversation).where(
                Conversation.whatsapp_number_hash == phone_hash,
                Conversation.status == ConversationStatus.ACTIVE,
            )
        )
        if conversation is not None:
            return conversation

        conversation = Conversation(whatsapp_number_hash=phone_hash, status=ConversationStatus.ACTIVE)
        self.db.add(conversation)
        await self.db.flush()
        return conversation

    def _hash_number(self, number: str) -> str:
        material = f'{number}{self.settings.hash_salt}'
        return hashlib.sha256(material.encode('utf-8')).hexdigest()
