from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.modules.whatsapp.client import MetaAPIClient
from src.modules.whatsapp.credentials import resolve_whatsapp_graph_credentials


async def create_meta_api_client(db: AsyncSession, settings: Settings) -> MetaAPIClient:
    phone_id, token = await resolve_whatsapp_graph_credentials(db, settings)
    return MetaAPIClient.from_phone_and_token(phone_id, token)
