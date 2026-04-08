from __future__ import annotations

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import require_api_key
from src.dependencies import get_db_session
from src.modules.settings.service import SettingsService

router = APIRouter(prefix='/settings', tags=['settings'], dependencies=[Depends(require_api_key)])


@router.get('/{category}', status_code=status.HTTP_200_OK)
async def category(category: str = Path(pattern='^(bot|ai|whatsapp|notifications)$'), db: AsyncSession = Depends(get_db_session)) -> list[dict]:
    items = await SettingsService(db).get_category(category)
    return [{'id': i.id, 'key': i.key, 'value': i.value, 'category': i.category} for i in items]


@router.put('/{key}', status_code=status.HTTP_200_OK)
async def update(key: str, payload: dict, db: AsyncSession = Depends(get_db_session)) -> dict:
    s = await SettingsService(db).update(key, payload.get('value', {}))
    return {'id': s.id, 'key': s.key, 'value': s.value, 'category': s.category}
