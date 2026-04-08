from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import require_api_key
from src.dependencies import get_db_session
from src.modules.analytics.schemas import KPIResponse
from src.modules.analytics.service import AnalyticsService

router = APIRouter(prefix='/analytics', tags=['analytics'], dependencies=[Depends(require_api_key)])


@router.get('/kpis', response_model=KPIResponse, status_code=status.HTTP_200_OK)
async def kpis(db: AsyncSession = Depends(get_db_session)) -> KPIResponse:
    return KPIResponse(**(await AnalyticsService(db).kpis()))
