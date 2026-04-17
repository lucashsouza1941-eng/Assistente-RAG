from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.core.security import require_api_key
from src.dependencies import get_db_session, get_settings
from src.modules.settings.service import SettingsService
from src.modules.whatsapp.credentials import resolve_whatsapp_graph_credentials
from src.modules.whatsapp.factory import create_meta_api_client
from src.modules.whatsapp.schemas import WhatsAppConnectionResponse, WhatsAppCredentialsPayload

router = APIRouter(
    prefix='/whatsapp/admin',
    tags=['whatsapp-admin'],
    dependencies=[Depends(require_api_key)],
)

COMMON = {
    401: {'description': 'API key ausente'},
    403: {'description': 'API key invalida'},
}


@router.get(
    '/connection',
    response_model=WhatsAppConnectionResponse,
    status_code=status.HTTP_200_OK,
    responses=COMMON,
)
async def connection_status(
    db: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> WhatsAppConnectionResponse:
    phone_id, _ = await resolve_whatsapp_graph_credentials(db, settings)
    vals = await SettingsService(db).get_category_values('whatsapp')
    has_vt = bool(str(vals.get('verify_token') or '').strip()) or bool(
        settings.whatsapp_verify_token,
    )
    has_tok = bool(str(vals.get('access_token') or '').strip()) or bool(
        settings.whatsapp_access_token,
    )

    base = (settings.public_api_base_url or '').rstrip('/')
    webhook_url = f'{base}/whatsapp/webhook' if base else None

    client = await create_meta_api_client(db, settings)
    try:
        profile = await client.fetch_phone_number_profile()
        return WhatsAppConnectionResponse(
            connected=True,
            phone_number_id=str(profile.get('id', phone_id)),
            verified_name=profile.get('verified_name'),
            display_phone_number=profile.get('display_phone_number'),
            quality_rating=profile.get('quality_rating'),
            messaging_limit_tier=profile.get('messaging_limit_tier'),
            public_webhook_url=webhook_url,
            verify_token_configured=has_vt,
            access_token_configured=has_tok,
        )
    except Exception as exc:
        return WhatsAppConnectionResponse(
            connected=False,
            phone_number_id=phone_id,
            error=str(exc)[:500],
            public_webhook_url=webhook_url,
            verify_token_configured=has_vt,
            access_token_configured=has_tok,
        )
    finally:
        await client.aclose()


@router.put('/credentials', status_code=status.HTTP_200_OK, responses=COMMON)
async def put_credentials(
    payload: WhatsAppCredentialsPayload,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    """Persiste credenciais opcionais na tabela `settings` (chaves `whatsapp.*`)."""
    svc = SettingsService(db)
    if payload.phone_number_id is not None:
        await svc.update('whatsapp.phone_number_id', {'v': payload.phone_number_id.strip()})
    if payload.access_token is not None:
        await svc.update('whatsapp.access_token', {'v': payload.access_token.strip()})
    if payload.verify_token is not None:
        await svc.update('whatsapp.verify_token', {'v': payload.verify_token.strip()})
    return {'status': 'ok'}
