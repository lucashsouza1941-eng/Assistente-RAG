from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from fastapi.responses import PlainTextResponse
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.dependencies import get_db_session, get_redis, get_settings
from src.modules.whatsapp.schemas import WebhookPayload
from src.modules.whatsapp.service import WhatsAppService
from src.modules.whatsapp.validators import validate_webhook_signature

router = APIRouter(prefix='/whatsapp', tags=['whatsapp'])
logger = get_logger(__name__)


@router.get('/webhook')
async def verify_webhook(
    hub_mode: str = Query(alias='hub.mode'),
    hub_verify_token: str = Query(alias='hub.verify_token'),
    hub_challenge: str = Query(alias='hub.challenge'),
    settings=Depends(get_settings),
) -> PlainTextResponse:
    if hub_mode == 'subscribe' and hub_verify_token == settings.whatsapp_verify_token:
        return PlainTextResponse(content=hub_challenge, status_code=200)
    return PlainTextResponse(content='Forbidden', status_code=403)


@router.post('/webhook', dependencies=[Depends(validate_webhook_signature)])
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis),
    settings=Depends(get_settings),
) -> PlainTextResponse:
    payload = WebhookPayload.model_validate_json((await request.body()).decode('utf-8'))

    if payload.message is None:
        return PlainTextResponse(content='ok', status_code=200)

    if payload.message.type != 'text' or payload.message.text is None:
        logger.info('whatsapp.ignored_non_text', message_type=payload.message.type, message_id=payload.message.id)
        return PlainTextResponse(content='ok', status_code=200)

    service = WhatsAppService(db=db, redis=redis, settings=settings)
    background_tasks.add_task(service.handle_message, payload.message)
    return PlainTextResponse(content='ok', status_code=200)
