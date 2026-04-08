from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request, status
from fastapi.responses import PlainTextResponse
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db_session, get_redis, get_settings
from src.modules.whatsapp.schemas import WebhookPayload
from src.modules.whatsapp.service import WhatsAppService
from src.modules.whatsapp.validators import validate_webhook_signature

router = APIRouter(prefix='/whatsapp', tags=['whatsapp'])


# Webhook da Meta nao envia X-API-Key. Esta rota e publica por design e
# autenticada exclusivamente via verificacao HMAC SHA256 da assinatura.
@router.get('/webhook', response_class=PlainTextResponse, status_code=status.HTTP_200_OK)
async def verify(
    hub_mode: str = Query(alias='hub.mode'),
    hub_verify_token: str = Query(alias='hub.verify_token'),
    hub_challenge: str = Query(alias='hub.challenge'),
    settings=Depends(get_settings),
) -> PlainTextResponse:
    if hub_mode == 'subscribe' and hub_verify_token == settings.whatsapp_verify_token:
        return PlainTextResponse(hub_challenge, status_code=200)
    return PlainTextResponse('Forbidden', status_code=403)


@router.post(
    '/webhook',
    response_class=PlainTextResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(validate_webhook_signature)],
)
async def webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis),
    settings=Depends(get_settings),
) -> PlainTextResponse:
    payload = WebhookPayload.model_validate_json((await request.body()).decode('utf-8'))
    if payload.message and payload.message.type == 'text' and payload.message.text:
        background_tasks.add_task(WhatsAppService(db, redis, settings).handle_message, payload.message)
    return PlainTextResponse('ok', status_code=200)
