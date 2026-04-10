from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request, status
from fastapi.responses import PlainTextResponse
from redis.asyncio import Redis

from src.config import Settings
from src.dependencies import get_meta_api_client, get_redis, get_settings
from src.modules.whatsapp.client import MetaAPIClient
from src.modules.whatsapp.schemas import WebhookAckResponse, WebhookPayload
from src.modules.whatsapp.service import WhatsAppService
from src.modules.whatsapp.validators import validate_webhook_signature

router = APIRouter(prefix='/whatsapp', tags=['whatsapp'])


@router.get('/webhook', response_class=PlainTextResponse, status_code=status.HTTP_200_OK, responses={403: {'description': 'Token de verificacao invalido'}, 422: {'description': 'Validacao falhou'}})
async def verify(hub_mode: str = Query(alias='hub.mode'), hub_verify_token: str = Query(alias='hub.verify_token'), hub_challenge: str = Query(alias='hub.challenge'), settings=Depends(get_settings)) -> PlainTextResponse:
    if hub_mode == 'subscribe' and hub_verify_token == settings.whatsapp_verify_token:
        return PlainTextResponse(hub_challenge, status_code=200)
    return PlainTextResponse('Forbidden', status_code=403)


@router.post('/webhook', response_model=WebhookAckResponse, status_code=status.HTTP_200_OK, dependencies=[Depends(validate_webhook_signature)], responses={403: {'description': 'Assinatura invalida'}, 422: {'description': 'Validacao falhou'}})
async def webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
    meta_client: MetaAPIClient = Depends(get_meta_api_client),
) -> WebhookAckResponse:
    payload = WebhookPayload.model_validate_json((await request.body()).decode('utf-8'))
    if payload.message and payload.message.type == 'text' and payload.message.text:
        background_tasks.add_task(WhatsAppService(meta_client).handle_message, payload.message, redis, settings)
    return WebhookAckResponse(message='ok')
