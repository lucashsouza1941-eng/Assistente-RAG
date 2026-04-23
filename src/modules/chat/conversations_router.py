from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.core.security import require_api_key
from src.dependencies import get_db_session, get_redis, get_settings
from src.modules.chat.schemas import UnreadCountResponse
from src.modules.chat.service import ConversationService

COMMON_AUTH_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {'description': 'API key ausente'},
    403: {'description': 'API key invalida'},
    422: {'description': 'Validacao falhou'},
}

router = APIRouter(prefix='/conversations', tags=['conversations'], dependencies=[Depends(require_api_key)])


@router.get(
    '/unread-count',
    response_model=UnreadCountResponse,
    status_code=status.HTTP_200_OK,
    responses=COMMON_AUTH_RESPONSES,
)
async def unread_count(
    db: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> UnreadCountResponse:
    n = await ConversationService(db, redis, settings).count_unread()
    return UnreadCountResponse(count=n)
