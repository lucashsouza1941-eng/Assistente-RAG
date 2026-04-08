from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import require_api_key
from src.dependencies import get_db_session
from src.modules.analytics.schemas import CategoryPoint, KPIResponse, QuestionCount, VolumePoint
from src.modules.analytics.service import AnalyticsService

router = APIRouter(prefix='/analytics', tags=['analytics'], dependencies=[Depends(require_api_key)])

@router.get('/kpis', response_model=KPIResponse, status_code=status.HTTP_200_OK, responses={401: {'description': 'Unauthorized'}})
async def get_kpis(period: str = Query(default='today', pattern='^(today|7d|30d)$'), db: AsyncSession = Depends(get_db_session)) -> KPIResponse:
    return KPIResponse(**(await AnalyticsService(db).get_kpis(period)))

@router.get('/volume', response_model=list[VolumePoint], status_code=status.HTTP_200_OK, responses={401: {'description': 'Unauthorized'}})
async def get_volume(granularity: str = Query(default='day', pattern='^(hour|day)$'), db: AsyncSession = Depends(get_db_session)) -> list[VolumePoint]:
    return [VolumePoint(**row) for row in await AnalyticsService(db).get_volume(granularity)]

@router.get('/categories', response_model=list[CategoryPoint], status_code=status.HTTP_200_OK, responses={401: {'description': 'Unauthorized'}})
async def get_categories(db: AsyncSession = Depends(get_db_session)) -> list[CategoryPoint]:
    return [CategoryPoint(**row) for row in await AnalyticsService(db).get_categories()]

@router.get('/top-questions', response_model=list[QuestionCount], status_code=status.HTTP_200_OK, responses={401: {'description': 'Unauthorized'}})
async def get_top_questions(limit: int = Query(default=10, ge=1, le=100), db: AsyncSession = Depends(get_db_session)) -> list[QuestionCount]:
    return [QuestionCount(**row) for row in await AnalyticsService(db).get_top_questions(limit)]
