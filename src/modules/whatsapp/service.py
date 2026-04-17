from __future__ import annotations

import hashlib
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.core.logging import get_logger, sanitize_message
from src.core.metrics import KEY_WHATSAPP_HANDLER_FAILED, incr, log_metric_event
from src.dependencies import AsyncSessionLocal
from src.modules.chat.models import Conversation, ConversationStatus, Message, MessageRole
from src.modules.chat.rag_chain import RAGChain
from src.modules.whatsapp.factory import create_meta_api_client
from src.modules.whatsapp.schemas import WebhookMessage

log = get_logger(module='whatsapp.service')


class WhatsAppService:
    @staticmethod
    async def handle_message(message: WebhookMessage, redis: Redis, settings: Settings) -> None:
        conversation_id: UUID | None = None
        meta_client = None
        try:
            async with AsyncSessionLocal() as db:
                meta_client = await create_meta_api_client(db, settings)
                async with db.begin():
                    number_hash = hashlib.sha256(f'{message.from_}{settings.hash_salt}'.encode()).hexdigest()
                    if not await WhatsAppService._allow(redis, number_hash):
                        return
                    conv = await WhatsAppService._conversation(db, number_hash)
                    conversation_id = conv.id
                    text = message.text.body if message.text else ''
                    db.add(Message(conversation_id=conv.id, role=MessageRole.USER, content=text))
                    rag = await RAGChain.from_settings(db, settings)
                    response = await rag.generate(text, conv.id)
                    db.add(
                        Message(
                            conversation_id=conv.id,
                            role=MessageRole.ASSISTANT,
                            content=response.content,
                            sources_used=response.sources,
                            confidence=response.confidence,
                            response_time_ms=response.response_time_ms,
                        )
                    )
                    if response.escalated:
                        conv.status = ConversationStatus.ESCALATED
                await meta_client.send_text_message(message.from_, response.content)
                await meta_client.mark_as_read(message.id)
                log.info('whatsapp.handled', metadata={'number_hash': number_hash, 'message_preview': sanitize_message(text)})
        except Exception as exc:
            await incr(redis, KEY_WHATSAPP_HANDLER_FAILED)
            log_metric_event('whatsapp_handler_failed', error_type=type(exc).__name__)
            log.error(
                'whatsapp_message_handling_failed',
                error_type=type(exc).__name__,
                error_message=str(exc)[:200],
                conversation_id=str(conversation_id) if conversation_id else None,
            )
            raise
        finally:
            if meta_client is not None:
                await meta_client.aclose()

    @staticmethod
    async def _allow(redis: Redis, number_hash: str) -> bool:
        key = f'rate:{number_hash}'
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, 60)
        return count <= 20

    @staticmethod
    async def _conversation(db: AsyncSession, number_hash: str) -> Conversation:
        conv = await db.scalar(select(Conversation).where(Conversation.whatsapp_number_hash == number_hash, Conversation.status == ConversationStatus.ACTIVE))
        if conv:
            return conv
        conv = Conversation(whatsapp_number_hash=number_hash)
        db.add(conv)
        await db.flush()
        return conv
