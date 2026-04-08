from __future__ import annotations

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import require_api_key
from src.dependencies import get_db_session
from src.modules.settings.schemas import SettingResponse, SettingUpdate
from src.modules.settings.service import SettingsService

router = APIRouter(prefix='/settings', tags=['settings'], dependencies=[Depends(require_api_key)])

@router.get('/{category}', response_model=list[SettingResponse], status_code=status.HTTP_200_OK, responses={401: {'description': 'Unauthorized'}})
async def get_settings_by_category(category: str = Path(pattern='^(bot|ai|whatsapp|notifications)$'), db: AsyncSession = Depends(get_db_session)) -> list[SettingResponse]:
    items = await SettingsService(db).get_by_category(category)
    return [SettingResponse(id=s.id, key=s.key, value=s.value, category=s.category) for s in items]

@router.put('/{key}', response_model=SettingResponse, status_code=status.HTTP_200_OK, responses={401: {'description': 'Unauthorized'}})
async def update_setting(key: str, payload: SettingUpdate, db: AsyncSession = Depends(get_db_session)) -> SettingResponse:
    s = await SettingsService(db).update(key, payload.value)
    return SettingResponse(id=s.id, key=s.key, value=s.value, category=s.category)
