from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db_session, get_redis, get_settings
from src.modules.chat.schemas import ChatRequest, ChatResponse
from src.modules.chat.service import ConversationService

router = APIRouter(prefix='/chat', tags=['chat'])


@router.post('/ask', response_model=ChatResponse)
async def ask(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis),
    settings=Depends(get_settings),
) -> ChatResponse:
    service = ConversationService(db, redis, settings)
    response = await service.answer(payload.question, UUID(payload.conversation_id))
    return ChatResponse(
        content=response.content,
        sources=response.sources,
        confidence=response.confidence,
        escalated=response.escalated,
        response_time_ms=response.response_time_ms,
    )
