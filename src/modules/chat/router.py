from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import require_api_key
from src.dependencies import get_db_session, get_redis, get_settings
from src.modules.chat.schemas import ChatRequest, ChatResponse, ConversationPage, ConversationResponse, MessageResponse, PeriodFilter
from src.modules.chat.service import ConversationService

COMMON_AUTH_RESPONSES = {
    401: {'description': 'API key ausente'},
    403: {'description': 'API key invalida'},
    422: {'description': 'Validacao falhou'},
}

router = APIRouter(prefix='/chat', tags=['chat'], dependencies=[Depends(require_api_key)])


@router.post('/message', response_model=ChatResponse, status_code=status.HTTP_200_OK, responses=COMMON_AUTH_RESPONSES)
async def message(payload: ChatRequest, db: AsyncSession = Depends(get_db_session), redis: Redis = Depends(get_redis), settings=Depends(get_settings)) -> ChatResponse:
    conv, resp = await ConversationService(db, redis, settings).send(payload.message, UUID(payload.conversation_id) if payload.conversation_id else None)
    return ChatResponse(reply=resp.content, sources=resp.sources, confidence=resp.confidence, escalated=resp.escalated, conversation_id=str(conv.id), response_time_ms=resp.response_time_ms)


@router.get('/conversations', response_model=ConversationPage, status_code=status.HTTP_200_OK, responses=COMMON_AUTH_RESPONSES)
async def conversations(page: int = Query(default=1, ge=1), size: int = Query(default=20, ge=1, le=100), period: PeriodFilter | None = Query(default=None), db: AsyncSession = Depends(get_db_session), redis: Redis = Depends(get_redis), settings=Depends(get_settings)) -> ConversationPage:
    items, total = await ConversationService(db, redis, settings).list_conversations(page, size, period)
    pages = (total + size - 1) // size if total else 0
    return ConversationPage(items=[ConversationResponse(id=str(i.id), status=i.status, started_at=i.started_at) for i in items], total=total, page=page, size=size, pages=pages)


@router.get('/conversations/{conversation_id}/messages', response_model=list[MessageResponse], status_code=status.HTTP_200_OK, responses={**COMMON_AUTH_RESPONSES, 404: {'description': 'Recurso nao encontrado'}})
async def messages(conversation_id: UUID, db: AsyncSession = Depends(get_db_session), redis: Redis = Depends(get_redis), settings=Depends(get_settings)) -> list[MessageResponse]:
    svc = ConversationService(db, redis, settings)
    try:
        items = await svc.list_messages(conversation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [MessageResponse(id=str(m.id), role=m.role, content=m.content, created_at=m.created_at) for m in items]
