from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import require_api_key
from src.dependencies import get_db_session
from src.modules.analytics.schemas import CategoryPoint, KPIResponse, QuestionCount, VolumePoint
from src.modules.analytics.service import AnalyticsService

COMMON_AUTH_RESPONSES = {
    401: {'description': 'API key ausente'},
    403: {'description': 'API key invalida'},
    422: {'description': 'Validacao falhou'},
}

router = APIRouter(prefix='/analytics', tags=['analytics'], dependencies=[Depends(require_api_key)])


@router.get('/kpis', response_model=KPIResponse, status_code=status.HTTP_200_OK, responses=COMMON_AUTH_RESPONSES)
async def kpis(db: AsyncSession = Depends(get_db_session)) -> KPIResponse:
    return KPIResponse(**(await AnalyticsService(db).kpis()))


@router.get('/volume', response_model=list[VolumePoint], status_code=status.HTTP_200_OK, responses=COMMON_AUTH_RESPONSES)
async def volume(granularity: str = Query(default='day'), db: AsyncSession = Depends(get_db_session)) -> list[VolumePoint]:
    return [VolumePoint(timestamp='n/a', count=0)]


@router.get('/categories', response_model=list[CategoryPoint], status_code=status.HTTP_200_OK, responses=COMMON_AUTH_RESPONSES)
async def categories(db: AsyncSession = Depends(get_db_session)) -> list[CategoryPoint]:
    return [CategoryPoint(category='outros', count=0, percentage=0.0)]


@router.get('/top-questions', response_model=list[QuestionCount], status_code=status.HTTP_200_OK, responses=COMMON_AUTH_RESPONSES)
async def top_questions(limit: int = Query(default=10, ge=1, le=100), db: AsyncSession = Depends(get_db_session)) -> list[QuestionCount]:
    return [QuestionCount(question_preview='Sem dados', count=0)]
