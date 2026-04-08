from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import require_api_key
from src.dependencies import get_db_session
from src.modules.settings.schemas import SettingResponse, SettingUpdate
from src.modules.settings.service import SettingsService

COMMON_AUTH_RESPONSES = {
    401: {'description': 'API key ausente'},
    403: {'description': 'API key invalida'},
    422: {'description': 'Validacao falhou'},
}

router = APIRouter(prefix='/settings', tags=['settings'], dependencies=[Depends(require_api_key)])


@router.get('/{category}', response_model=list[SettingResponse], status_code=status.HTTP_200_OK, responses={**COMMON_AUTH_RESPONSES, 404: {'description': 'Recurso nao encontrado'}})
async def category(category: str = Path(pattern='^(bot|ai|whatsapp|notifications)$'), db: AsyncSession = Depends(get_db_session)) -> list[SettingResponse]:
    items = await SettingsService(db).get_category(category)
    if not items:
        raise HTTPException(status_code=404, detail=f'Nenhuma configuracao encontrada para a categoria {category}')
    return [SettingResponse(id=i.id, key=i.key, value=i.value, category=i.category) for i in items]


@router.put('/{key}', response_model=SettingResponse, status_code=status.HTTP_200_OK, responses=COMMON_AUTH_RESPONSES)
async def update(key: str, payload: SettingUpdate, db: AsyncSession = Depends(get_db_session)) -> SettingResponse:
    s = await SettingsService(db).update(key, payload.value)
    return SettingResponse(id=s.id, key=s.key, value=s.value, category=s.category)
