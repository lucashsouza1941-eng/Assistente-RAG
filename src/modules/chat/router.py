from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import require_api_key
from src.dependencies import get_db_session, get_redis, get_settings
from src.modules.chat.models import ConversationStatus
from src.modules.chat.schemas import ChatRequest, ChatResponse, ConversationPage, ConversationResponse, MessageResponse
from src.modules.chat.service import ConversationService

router = APIRouter(prefix='/chat', tags=['chat'], dependencies=[Depends(require_api_key)])


@router.post('/message', response_model=ChatResponse, status_code=status.HTTP_200_OK, responses={401: {'description': 'Unauthorized'}})
async def send_message(payload: ChatRequest, db: AsyncSession = Depends(get_db_session), redis: Redis = Depends(get_redis), settings=Depends(get_settings)) -> ChatResponse:
    service = ConversationService(db, redis, settings)
    conv_id = UUID(payload.conversation_id) if payload.conversation_id else None
    conversation, response = await service.send_message(payload.message, conv_id)
    return ChatResponse(reply=response.content, sources=response.sources, confidence=response.confidence, escalated=response.escalated, conversation_id=str(conversation.id), response_time_ms=response.response_time_ms)


@router.get('/conversations', response_model=ConversationPage, status_code=status.HTTP_200_OK, responses={401: {'description': 'Unauthorized'}})
async def list_conversations(page: int = Query(default=1, ge=1), size: int = Query(default=20, ge=1, le=100), status_filter: ConversationStatus | None = Query(default=None, alias='status'), period: str | None = Query(default=None), db: AsyncSession = Depends(get_db_session), redis: Redis = Depends(get_redis), settings=Depends(get_settings)) -> ConversationPage:
    service = ConversationService(db, redis, settings)
    items, total = await service.list_conversations(page=page, size=size, status=status_filter, period=period)
    return ConversationPage(items=[ConversationResponse(id=str(i.id), status=i.status, started_at=i.started_at, last_message_at=i.last_message_at, message_count=i.message_count, resolved_without_human=i.resolved_without_human) for i in items], total=total, page=page, size=size)


@router.get('/conversations/{conversation_id}/messages', response_model=list[MessageResponse], status_code=status.HTTP_200_OK, responses={401: {'description': 'Unauthorized'}, 404: {'description': 'Conversation not found'}})
async def list_messages(conversation_id: UUID, db: AsyncSession = Depends(get_db_session), redis: Redis = Depends(get_redis), settings=Depends(get_settings)) -> list[MessageResponse]:
    service = ConversationService(db, redis, settings)
    if not await service.conversation_exists(conversation_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Conversation not found')
    msgs = await service.list_messages(conversation_id)
    return [MessageResponse(id=str(m.id), role=m.role, content=m.content, sources_used=m.sources_used, confidence=m.confidence, response_time_ms=m.response_time_ms, created_at=m.created_at) for m in msgs]
