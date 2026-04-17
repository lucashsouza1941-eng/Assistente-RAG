from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.modules.settings.service import SettingsService


async def resolve_whatsapp_graph_credentials(db: AsyncSession, settings: Settings) -> tuple[str, str]:
    """Phone Number ID e access token: overrides em `settings` (whatsapp.*) ou variáveis de ambiente."""
    svc = SettingsService(db)
    vals = await svc.get_category_values('whatsapp')
    pid = vals.get('phone_number_id')
    tok = vals.get('access_token')
    phone_id = str(pid).strip() if pid not in (None, '') else settings.whatsapp_phone_number_id
    token = str(tok).strip() if tok not in (None, '') else settings.whatsapp_access_token
    return phone_id, token


async def resolve_whatsapp_verify_token(db: AsyncSession, settings: Settings) -> str:
    """Token de verificação do webhook GET (Meta): DB `whatsapp.verify_token` ou env."""
    svc = SettingsService(db)
    vals = await svc.get_category_values('whatsapp')
    vt = vals.get('verify_token')
    if vt is not None and str(vt).strip() != '':
        return str(vt).strip()
    return settings.whatsapp_verify_token
