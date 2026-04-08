from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import require_api_key
from src.dependencies import get_db_session, get_redis, get_settings
from src.modules.chat.schemas import ChatRequest, ChatResponse
from src.modules.chat.service import ConversationService

router = APIRouter(prefix='/chat', tags=['chat'], dependencies=[Depends(require_api_key)])


@router.post('/message', response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def message(payload: ChatRequest, db: AsyncSession = Depends(get_db_session), redis: Redis = Depends(get_redis), settings=Depends(get_settings)) -> ChatResponse:
    conv, resp = await ConversationService(db, redis, settings).send(payload.message, UUID(payload.conversation_id) if payload.conversation_id else None)
    return ChatResponse(reply=resp.content, sources=resp.sources, confidence=resp.confidence, escalated=resp.escalated, conversation_id=str(conv.id), response_time_ms=resp.response_time_ms)
